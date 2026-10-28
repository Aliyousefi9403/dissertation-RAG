import { test, expect, type Page, type Route } from "@playwright/test";

import { askQuestion, waitForBackendOnline } from "./utils";

/**
 * UI-state tests for the experimental Evidence check. The backend is
 * mocked at the browser level (`page.route`), so these prove only that the
 * interface renders each real response shape honestly — they do NOT
 * demonstrate live verification. Needs only the Next.js dev server.
 */

const QUESTION = "How can SQL injection be prevented?";
const SQLI = "Parameterized queries prevent SQL injection.";

function guardedResponse(overrides: Record<string, unknown> = {}) {
  return {
    run_id: "20261016T220000Z-test",
    question: QUESTION,
    system_state: "clean",
    policy_version: "evidence-guard-policy-v1",
    label:
      "Experimental evidence-support baseline. Not a validated poison detector: a poisoned source can support a false answer.",
    outcome: "supported",
    decision: "released",
    answer: "Use parameterized queries [Source 1].",
    explanation: "All 1 claim(s) are stated in the retrieved sources.",
    claims: [
      {
        claim: "Parameterized queries prevent SQL injection.",
        status: "supported",
        verifier_verdict: "supported",
        source_ids: ["S1"],
        quotes: [{ source_id: "S1", text: SQLI, verified: true }],
        explanation: "S1 states this.",
        problems: [],
      },
    ],
    sources: [
      {
        source_id: "S1",
        source_number: 1,
        source: "injection/sql_injection.md",
        score: 0.82,
        content: SQLI,
        metadata: {},
      },
    ],
    failures: [],
    audit: { saved: true, run_id: "20261016T220000Z-test", location: "/x.json", error: null },
    timings_ms: { retrieval_ms: 10, draft_ms: 900, verification_ms: 800, total_ms: 1710 },
    ...overrides,
  };
}

async function mockBackend(
  page: Page,
  guarded: (route: Route) => Promise<void> | void,
  calls: string[] = [],
) {
  await page.route("**/health", (route) =>
    route.fulfill({ json: { status: "healthy" } }),
  );
  await page.route("**/guarded-chat", async (route) => {
    calls.push("guarded-chat");
    await guarded(route);
  });
  await page.route("**/chat", (route) => {
    calls.push("chat");
    return route.fulfill({
      json: {
        question: QUESTION,
        answer: "Plain baseline answer.",
        sources: guardedResponse().sources,
        system_state: "clean",
      },
    });
  });
}

async function enableEvidenceCheck(page: Page) {
  const toggle = page.getByRole("switch", { name: "Evidence check" });
  await toggle.click();
  await expect(toggle).toHaveAttribute("aria-checked", "true");
}

const resolved = (page: Page) =>
  expect(page.locator(".evidence-check-card, .error-card, .answer-text").first()).toBeVisible({
    timeout: 15_000,
  });

test.describe("Evidence check (mocked backend)", () => {
  test("supported: draft released with the real outcome and no invented scores", async ({ page }) => {
    const calls: string[] = [];
    await mockBackend(page, (route) => route.fulfill({ json: guardedResponse() }), calls);
    await page.goto("/");
    await waitForBackendOnline(page);
    await enableEvidenceCheck(page);
    await askQuestion(page, QUESTION);
    await resolved(page);

    await expect(page.locator(".answer-text")).toContainText("Use parameterized queries");
    const card = page.locator(".evidence-check-card");
    await expect(card).toHaveAttribute("data-outcome", "supported");
    await expect(card).toContainText("Claims are stated in the retrieved sources");
    await expect(card).toContainText("Not a validated poison detector");
    await expect(card).toContainText("Audit record saved");
    await expect(page.locator(".report-chip-row")).toContainText("Supported");
    expect(calls).toEqual(["guarded-chat"]);

    const body = await page.locator("body").innerText();
    expect(body).not.toMatch(/confidence|trust score|documents indexed/i);
    expect(body).not.toMatch(/\d+%/);
  });

  test("unsupported/contradicted: draft withheld with explanation and failed quotes", async ({ page }) => {
    await mockBackend(page, (route) =>
      route.fulfill({
        json: guardedResponse({
          outcome: "contradicted",
          decision: "withheld",
          answer: null,
          explanation: "1 claim(s) are contradicted by the retrieved sources.",
          claims: [
            {
              claim: "Input validation alone always stops SQL injection.",
              status: "unavailable",
              verifier_verdict: "contradicted",
              source_ids: ["S1"],
              quotes: [{ source_id: "S1", text: "validation is always enough", verified: false }],
              explanation: "",
              problems: ["a quotation was not found verbatim in the cited source"],
            },
          ],
        }),
      }),
    );
    await page.goto("/");
    await waitForBackendOnline(page);
    await enableEvidenceCheck(page);
    await askQuestion(page, QUESTION);
    await resolved(page);

    await expect(page.locator(".answer-text")).toHaveCount(0);
    await expect(page.locator(".answer-withheld")).toBeVisible();
    const card = page.locator(".evidence-check-card");
    await expect(card).toHaveAttribute("data-outcome", "contradicted");
    await expect(card).toContainText("Draft withheld");
    await expect(card).toContainText("Input validation alone always stops SQL injection.");
    await expect(card).toContainText("Not found in source");
    await expect(card).toContainText("not found verbatim");
  });

  test("unavailable: verifier timeout and unsaved audit are shown as warnings", async ({ page }) => {
    await mockBackend(page, (route) =>
      route.fulfill({
        json: guardedResponse({
          outcome: "unavailable",
          decision: "withheld",
          answer: null,
          claims: [],
          explanation: "The evidence check could not be completed, so the draft is withheld.",
          failures: [{ stage: "verification", type: "APITimeoutError", timeout: true }],
          audit: {
            saved: false,
            run_id: "r",
            location: null,
            error: "PermissionError: audit record was NOT saved",
          },
        }),
      }),
    );
    await page.goto("/");
    await waitForBackendOnline(page);
    await enableEvidenceCheck(page);
    await askQuestion(page, QUESTION);
    await resolved(page);

    const card = page.locator(".evidence-check-card");
    await expect(card).toHaveAttribute("data-outcome", "unavailable");
    await expect(card).toContainText("evidence check unavailable");
    await expect(card).toContainText("Verification failed (timed out)");
    await expect(card.locator(".evidence-check-audit")).toHaveAttribute("data-saved", "false");
    await expect(card).toContainText("Audit record NOT saved");
    await expect(page.locator(".report-chip-row")).toContainText("Unavailable");
    await expect(page.locator(".answer-text")).toHaveCount(0);
  });

  test("abstained: a refusal is released and labelled, not treated as an error", async ({ page }) => {
    await mockBackend(page, (route) =>
      route.fulfill({
        json: guardedResponse({
          outcome: "abstained",
          decision: "released",
          answer: "The retrieved context does not describe HTTP flood attacks.",
          claims: [],
          explanation:
            "The draft declines to answer because the retrieved sources are insufficient; it is released as a refusal, not as an answer.",
        }),
      }),
    );
    await page.goto("/");
    await waitForBackendOnline(page);
    await enableEvidenceCheck(page);
    await askQuestion(page, QUESTION);
    await resolved(page);

    await expect(page.locator(".answer-text")).toContainText("does not describe");
    const card = page.locator(".evidence-check-card");
    await expect(card).toHaveAttribute("data-outcome", "abstained");
    await expect(card).toContainText("sources were insufficient");
    await expect(page.locator(".report-chip-row")).toContainText("Abstained");
  });

  test("failure: a backend error renders the error card, not a result", async ({ page }) => {
    await mockBackend(page, (route) =>
      route.fulfill({ status: 500, json: { detail: "The evidence-checked request failed unexpectedly." } }),
    );
    await page.goto("/");
    await waitForBackendOnline(page);
    await enableEvidenceCheck(page);
    await askQuestion(page, QUESTION);
    await resolved(page);

    await expect(page.locator(".error-card")).toContainText("failed unexpectedly");
    await expect(page.locator(".evidence-check-card")).toHaveCount(0);
  });

  test("toggle off: plain /chat is used and the check reads Not assessed", async ({ page }) => {
    const calls: string[] = [];
    await mockBackend(page, (route) => route.fulfill({ json: guardedResponse() }), calls);
    await page.goto("/");
    await waitForBackendOnline(page);
    await askQuestion(page, QUESTION);
    await resolved(page);

    await expect(page.locator(".answer-text")).toContainText("Plain baseline answer.");
    await expect(page.locator(".report-chip-row")).toContainText("Not assessed");
    await expect(page.locator(".evidence-metrics")).toContainText("Not assessed");
    await expect(page.locator(".evidence-check-card")).toHaveCount(0);
    expect(calls).toEqual(["chat"]);
  });

  test("defended mode: /chat with system_state=defended, filter verdict shown, evidence check disabled", async ({ page }) => {
    const bodies: unknown[] = [];
    await page.route("**/health", (route) => route.fulfill({ json: { status: "healthy" } }));
    await page.route("**/chat", async (route) => {
      bodies.push(route.request().postDataJSON());
      await route.fulfill({
        json: {
          question: QUESTION,
          answer: "Use parameterized queries [Source 1].",
          system_state: "defended",
          sources: [
            {
              source_number: 1,
              source: "injection/sql_injection.md",
              score: 0.71,
              content: SQLI,
              metadata: {
                entropy_filter: {
                  policy_version: "entropy-filter-v1",
                  candidate_rank: 2,
                  score_bits: 3.42,
                  threshold_bits: 7.2262,
                  flagged: false,
                  top_words: [],
                },
              },
            },
          ],
        },
      });
    });
    await page.goto("/");
    await waitForBackendOnline(page);
    await expect(page.getByTestId("defence-shield")).toHaveCount(0);
    await page.getByRole("radio", { name: "Defended" }).click();
    await expect(page.getByTestId("defence-shield")).toBeVisible();
    await expect(page.getByTestId("defence-shield")).toContainText("armed");
    await expect(page.getByRole("switch", { name: "Evidence check" })).toBeDisabled();
    await expect(page.getByRole("status", { name: "Platform status" })).toContainText("PWWS poisoned + entropy filter");
    await askQuestion(page, QUESTION);
    await resolved(page);

    expect(bodies).toEqual([{ question: QUESTION, system_state: "defended" }]);
    await page.locator(".source-row-summary").first().click();
    await expect(page.locator(".source-row-filter")).toContainText("3.42 bits");
    await expect(page.locator(".source-row-filter")).toContainText("candidate rank 2");
    // One source kept at candidate rank 2 => exactly one candidate was skipped.
    await expect(page.getByTestId("defence-shield")).toContainText("1 suspicious passage blocked");
    await expect(page.locator(".defence-shield-token")).toHaveCount(1);
    await page.getByRole("radio", { name: "Clean" }).click();
    await expect(page.getByTestId("defence-shield")).toHaveCount(0);
  });

  test("repaired mode: /chat with system_state=repaired, repairs listed, evidence check disabled", async ({ page }) => {
    const bodies: unknown[] = [];
    await page.route("**/health", (route) => route.fulfill({ json: { status: "healthy" } }));
    await page.route("**/chat", async (route) => {
      bodies.push(route.request().postDataJSON());
      await route.fulfill({
        json: {
          question: QUESTION,
          answer: "Use parameterized queries [Source 1].",
          system_state: "repaired",
          sources: [
            {
              source_number: 1,
              source: "injection/sql_injection.md",
              score: 0.71,
              content: SQLI,
              metadata: {
                entropy_filter: {
                  policy_version: "entropy-repair-v1",
                  candidate_rank: 1,
                  score_bits: 4.1,
                  threshold_bits: 7.2262,
                  flagged: false,
                  top_words: [],
                  score_before_repair_bits: 10.75,
                  repairs: [
                    { word: "engraft", replacement: "plant", gap_bits: 14.1 },
                    { word: "abnegate", replacement: "deny", gap_bits: 18.58 },
                  ],
                },
              },
            },
          ],
        },
      });
    });
    await page.goto("/");
    await waitForBackendOnline(page);
    await page.getByRole("radio", { name: "Repaired" }).click();
    // Repaired has its own view (repair ledger), not the Defended shield.
    await expect(page.getByTestId("defence-shield")).toHaveCount(0);
    await expect(page.getByTestId("emblem-repair")).toContainText("Repair loom ready");
    await expect(page.getByRole("switch", { name: "Evidence check" })).toBeDisabled();
    await expect(page.getByRole("status", { name: "Platform status" })).toContainText("PWWS poisoned + entropy repair");
    await askQuestion(page, QUESTION);
    await resolved(page);

    expect(bodies).toEqual([{ question: QUESTION, system_state: "repaired" }]);
    await expect(page.getByTestId("emblem-repair")).toContainText("2 words restored");
    const ledger = page.getByTestId("repair-ledger");
    await expect(ledger).toContainText("2 words restored before the model read them");
    await expect(ledger.locator(".repair-change del")).toHaveText(["engraft", "abnegate"]);
    await expect(ledger.locator(".repair-change ins")).toHaveText(["plant", "deny"]);
    await expect(ledger).toContainText("10.75 → 4.10 bits");
    await page.locator(".source-row-summary").first().click();
    await expect(page.locator(".source-row-repairs")).toContainText("was 10.75 bits");
    await expect(page.locator(".source-row-repairs")).toContainText("engraft → plant, abnegate → deny");
  });

  test("contextual mode: /chat with system_state=contextual, filter verdict shown, evidence check disabled", async ({ page }) => {
    const bodies: unknown[] = [];
    await page.route("**/health", (route) => route.fulfill({ json: { status: "healthy" } }));
    await page.route("**/chat", async (route) => {
      bodies.push(route.request().postDataJSON());
      await route.fulfill({
        json: {
          question: QUESTION,
          answer: "Use parameterized queries [Source 1].",
          system_state: "contextual",
          sources: [
            {
              source_number: 1,
              source: "injection/sql_injection.md",
              score: 0.71,
              content: SQLI,
              metadata: {
                entropy_filter: {
                  policy_version: "contextual-filter-v1",
                  candidate_rank: 3,
                  score_bits: 1.87,
                  threshold_bits: 4.4611,
                  flagged: false,
                  top_words: [{ word: "abnegate", likely_original: "deny", gap_bits: 6.2 }],
                },
              },
            },
          ],
        },
      });
    });
    await page.goto("/");
    await waitForBackendOnline(page);
    await page.getByRole("radio", { name: "Contextual" }).click();
    // Contextual has its own view (context lens), not the Defended shield.
    await expect(page.getByTestId("defence-shield")).toHaveCount(0);
    await expect(page.getByTestId("emblem-lens")).toContainText("Context lens ready");
    await expect(page.getByRole("switch", { name: "Evidence check" })).toBeDisabled();
    await expect(page.getByRole("status", { name: "Platform status" })).toContainText("PWWS poisoned + language-model filter");
    await askQuestion(page, QUESTION);
    await resolved(page);

    expect(bodies).toEqual([{ question: QUESTION, system_state: "contextual" }]);
    await page.locator(".source-row-summary").first().click();
    await expect(page.locator(".source-row-filter")).toContainText("1.87 bits");
    // One source kept at candidate rank 3 => two candidates were skipped.
    await expect(page.getByTestId("emblem-lens")).toContainText("2 passages did not fit");
    const lens = page.getByTestId("context-lens");
    await expect(lens).toContainText("2 passages did not fit their context and were skipped");
    await expect(lens.locator(".context-word")).toContainText("abnegate");
    await expect(lens.locator(".context-word")).toContainText("→ deny");
  });

  test("verified mode: /chat with system_state=verified, monitor trace, memory and trusted fallback", async ({ page }) => {
    const bodies: unknown[] = [];
    await page.route("**/health", (route) => route.fulfill({ json: { status: "healthy" } }));
    // The memory holds the quarantined passage only after the question has been answered.
    await page.route("**/monitor/memory", (route) => {
      const answered = bodies.length > 0;
      return route.fulfill({
        json: {
          policy_version: "runtime-monitor-v2",
          count: answered ? 1 : 0,
          entries:
            answered
              ? [{ key: "abc", source: "malware/backdoor.md", words: ["engraft"], specs: ["phi1_lexical"],
                   question: QUESTION, round: 0, at: 1 }]
              : [],
        },
      });
    });
    await page.route("**/chat", async (route) => {
      bodies.push(route.request().postDataJSON());
      await route.fulfill({
        json: {
          question: QUESTION,
          answer: "The adversary implants malicious software [Source 1].",
          system_state: "verified",
          sources: [{ source_number: 1, source: "malware/backdoor.md", score: 0.7, content: SQLI, metadata: {} }],
          monitor: {
            policy_version: "runtime-monitor-v2",
            mode: "restore",
            attack: "backdoor",
            outcome: "released",
            generations: 2,
            trusted_fallback: true,
            final_violations: [],
            rounds: [
              {
                round: 0,
                skipped_quarantined: 0,
                answer: "Engraft Malicious Package",
                violations: [{ spec: "phi1_lexical", detail: "", witnesses: ["engraft"] }],
                quarantined: ["abc"],
              },
              { round: 1, skipped_quarantined: 1, answer: "ok", violations: [] },
            ],
          },
        },
      });
    });
    await page.goto("/");
    await waitForBackendOnline(page);
    await page.getByRole("radio", { name: "Verified" }).click();
    await expect(page.getByTestId("emblem-gate")).toContainText("Monitor armed");
    await page.getByRole("switch", { name: "Trusted fallback" }).click();
    await askQuestion(page, QUESTION);
    await resolved(page);

    expect(bodies).toEqual([{ question: QUESTION, system_state: "verified", trusted_fallback: true }]);
    const gate = page.getByTestId("emblem-gate");
    await expect(gate).toContainText("Monitor: verified · 1 quarantined");
    await expect(gate.locator('[data-node="fixed"]')).toHaveCount(2); // phi1 node and its link
    const trace = page.getByTestId("monitor-trace");
    await expect(trace).toContainText("Verified and released");
    await expect(trace.locator(".monitor-round")).toHaveCount(2);
    await expect(trace.locator(".monitor-witnesses")).toContainText("engraft");
    await expect(trace).toContainText("1 passage quarantined");
    await expect(page.getByTestId("monitor-memory")).toContainText("malware/backdoor.md");
  });

  test("compare mode disables the toggle; status bar shows only real values", async ({ page }) => {
    await mockBackend(page, (route) => route.fulfill({ json: guardedResponse() }));
    await page.goto("/");
    await waitForBackendOnline(page);

    const bar = page.getByRole("status", { name: "Platform status" });
    await expect(bar).toContainText("Reachable");
    await expect(bar).toContainText("Clean baseline");
    await expect(bar).toContainText("Not assessed");
    await expect(bar).not.toContainText("%");

    await page.getByRole("radio", { name: "Compare" }).click();
    await expect(page.getByRole("switch", { name: "Evidence check" })).toBeDisabled();
    await expect(bar).toContainText("Not available in Compare");
  });
});

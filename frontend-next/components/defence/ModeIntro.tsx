"use client";

const INTROS = {
  repaired: {
    variant: "repair",
    icon: "✎",
    title: "Repair ledger",
    text:
      "Each retrieved passage is scored for words that are much less likely than a synonym. " +
      "Words over 9.5 bits are swapped back to their likely original before the model reads " +
      "the passage. After you ask, the ledger shows every change as tracked edits.",
  },
  contextual: {
    variant: "context",
    icon: "◎",
    title: "Context lens",
    text:
      "A small language model reads each candidate passage and asks whether its words fit the " +
      "sentence. Passages over 4.46 bits are skipped. After you ask, the lens shows each passage's " +
      "score against the threshold and the words that fit worst.",
  },
  verified: {
    variant: "monitor",
    icon: "⌘",
    title: "Runtime monitor",
    text:
      "Every answer is checked against rules built from the official MITRE data. If a rule fails, " +
      "the passages responsible are quarantined, the model is told why, and it answers again. " +
      "Quarantined passages are remembered, so the same poison is not used twice.",
  },
} as const;

/** Shown before the first question in Repaired, Contextual and Verified modes. */
export function ModeIntro({ mode }: { mode: keyof typeof INTROS }) {
  const intro = INTROS[mode];
  return (
    <section
      className={`defence-view defence-view--${intro.variant} defence-view--intro`}
      aria-label={`${intro.title}: how this mode works`}
      data-testid="mode-intro"
    >
      <header className="defence-view-head">
        <span className="defence-view-icon" aria-hidden="true">
          {intro.icon}
        </span>
        <div>
          <p className="eyebrow">How this mode works</p>
          <h3>{intro.title}</h3>
        </div>
      </header>
      <p className="defence-view-text">{intro.text}</p>
    </section>
  );
}

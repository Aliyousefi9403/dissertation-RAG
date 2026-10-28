"use client";

import { useCallback, useReducer } from "react";

import { postChat } from "@/lib/api/chat";
import { postGuardedChat } from "@/lib/api/guardedChat";
import type { ApiFailureResult } from "@/lib/api/client";
import type { SystemState } from "@/lib/types/chat";
import { chatReducer, initialChatState, type ChatState } from "@/lib/state/chatMachine";

/** Shared with `hooks/useCompareSession.ts` so both hooks describe backend
 * failures identically. */
export function describeFailure(failure: ApiFailureResult): string {
  switch (failure.kind) {
    case "validationError":
      return typeof failure.detail === "string"
        ? failure.detail
        : "The question could not be validated. Please rephrase it and try again.";

    case "serverError":
      return failure.detail;

    case "networkError":
      return failure.message || "AegisRAG could not reach the backend. Make sure it is running.";

    case "timeout":
      return "The request took too long to complete. Please try again.";

    default: {
      const exhaustiveCheck: never = failure;
      return exhaustiveCheck;
    }
  }
}

export interface SubmitOptions {
  /** Route the question through the experimental `POST /guarded-chat`
   * evidence check instead of plain `POST /chat`. */
  evidenceCheck?: boolean;
  /** Verified mode: fall back to the trusted MITRE entry when a refusal cannot be fixed. */
  trustedFallback?: boolean;
}

export interface UseChatSessionResult {
  state: ChatState;
  submitQuestion: (
    question: string,
    systemState?: SystemState,
    options?: SubmitOptions,
  ) => Promise<void>;
  reset: () => void;
}

export function useChatSession(): UseChatSessionResult {
  const [state, dispatch] = useReducer(chatReducer, initialChatState);

  const submitQuestion = useCallback(
    async (question: string, systemState: SystemState = "clean", options: SubmitOptions = {}) => {
      const trimmed = question.trim();

      if (!trimmed) {
        return;
      }

      dispatch({ type: "SUBMIT_QUESTION", question: trimmed });

      // Real, measured latency for the round trip — never mocked.
      const startedAt = performance.now();

      if (options.evidenceCheck) {
        const guarded = await postGuardedChat(trimmed, systemState);
        const latencyMs = performance.now() - startedAt;

        if (guarded.kind === "ok") {
          const { question: q, answer, sources, ...evidenceCheck } = guarded.data;
          dispatch({
            type: "RESPONSE_RECEIVED",
            // A withheld draft is never sent to the client, so `answer`
            // is empty and the UI renders the withheld explanation instead.
            response: { question: q, answer: answer ?? "", sources },
            latencyMs,
            evidenceCheck,
          });
          return;
        }

        dispatch({ type: "REQUEST_FAILED", message: describeFailure(guarded) });
        return;
      }

      const result = await postChat(trimmed, systemState, {
        trustedFallback: options.trustedFallback,
      });
      const latencyMs = performance.now() - startedAt;

      if (result.kind === "ok") {
        dispatch({ type: "RESPONSE_RECEIVED", response: result.data, latencyMs });
        return;
      }

      dispatch({ type: "REQUEST_FAILED", message: describeFailure(result) });
    },
    [],
  );

  const reset = useCallback(() => {
    dispatch({ type: "RESET" });
  }, []);

  return { state, submitQuestion, reset };
}

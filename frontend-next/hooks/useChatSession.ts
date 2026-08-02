"use client";

import { useCallback, useReducer } from "react";

import { postChat } from "@/lib/api/chat";
import type { ApiFailureResult } from "@/lib/api/client";
import {
  chatReducer,
  initialChatState,
  type ChatState,
} from "@/lib/state/chatMachine";

function describeFailure(failure: ApiFailureResult): string {
  switch (failure.kind) {
    case "validationError":
      return typeof failure.detail === "string"
        ? failure.detail
        : "The question could not be validated. Please rephrase it and try again.";

    case "serverError":
      return failure.detail;

    case "networkError":
      return (
        failure.message ||
        "AegisRAG could not reach the backend. Make sure it is running."
      );

    case "timeout":
      return "The request took too long to complete. Please try again.";

    default: {
      const exhaustiveCheck: never = failure;
      return exhaustiveCheck;
    }
  }
}

export interface UseChatSessionResult {
  state: ChatState;
  submitQuestion: (question: string) => Promise<void>;
  reset: () => void;
}

export function useChatSession(): UseChatSessionResult {
  const [state, dispatch] = useReducer(chatReducer, initialChatState);

  const submitQuestion = useCallback(async (question: string) => {
    const trimmed = question.trim();

    if (!trimmed) {
      return;
    }

    dispatch({ type: "SUBMIT_QUESTION", question: trimmed });

    // Real, measured latency for the `POST /chat` round trip — never
    // mocked (see the boundary rules in the frontend implementation
    // brief). Everything else surfaced from this call (Confidence, Trust
    // Score, etc.) is illustrative mock data computed elsewhere.
    const startedAt = performance.now();
    const result = await postChat(trimmed);
    const latencyMs = performance.now() - startedAt;

    if (result.kind === "ok") {
      dispatch({ type: "RESPONSE_RECEIVED", response: result.data, latencyMs });
      return;
    }

    dispatch({ type: "REQUEST_FAILED", message: describeFailure(result) });
  }, []);

  const reset = useCallback(() => {
    dispatch({ type: "RESET" });
  }, []);

  return { state, submitQuestion, reset };
}

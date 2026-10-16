"use client";

import { useCallback, useReducer } from "react";

import { postCompare } from "@/lib/api/compare";
import { describeFailure } from "@/hooks/useChatSession";
import {
  compareReducer,
  initialCompareState,
  type CompareState,
} from "@/lib/state/compareMachine";

export interface UseCompareSessionResult {
  state: CompareState;
  submitComparison: (question: string) => Promise<void>;
  reset: () => void;
}

/** Drives `POST /compare` for Compare mode — mirrors `useChatSession`'s
 * shape/pattern but is a separate hook/state machine since the response
 * (clean + poisoned + metrics) has nothing in common with `ChatResponse`. */
export function useCompareSession(): UseCompareSessionResult {
  const [state, dispatch] = useReducer(compareReducer, initialCompareState);

  const submitComparison = useCallback(async (question: string) => {
    const trimmed = question.trim();

    if (!trimmed) {
      return;
    }

    dispatch({ type: "SUBMIT_COMPARISON", question: trimmed });

    const result = await postCompare(trimmed);

    if (result.kind === "ok") {
      dispatch({ type: "COMPARISON_RECEIVED", result: result.data });
      return;
    }

    dispatch({ type: "COMPARISON_FAILED", message: describeFailure(result) });
  }, []);

  const reset = useCallback(() => {
    dispatch({ type: "RESET" });
  }, []);

  return { state, submitComparison, reset };
}

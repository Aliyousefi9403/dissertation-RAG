import type { CompareResponse } from "@/lib/types/compare";

export type CompareState =
  | { status: "idle" }
  | { status: "submitting"; question: string }
  | { status: "success"; result: CompareResponse }
  | { status: "error"; question: string; message: string };

export type CompareEvent =
  | { type: "SUBMIT_COMPARISON"; question: string }
  | { type: "COMPARISON_RECEIVED"; result: CompareResponse }
  | { type: "COMPARISON_FAILED"; message: string }
  | { type: "RESET" };

export const initialCompareState: CompareState = { status: "idle" };

function assertNever(value: never): never {
  throw new Error(`Unhandled compare event: ${JSON.stringify(value)}`);
}

export function compareReducer(state: CompareState, event: CompareEvent): CompareState {
  switch (event.type) {
    case "SUBMIT_COMPARISON":
      return { status: "submitting", question: event.question };

    case "COMPARISON_RECEIVED": {
      if (state.status !== "submitting") {
        return state;
      }

      return { status: "success", result: event.result };
    }

    case "COMPARISON_FAILED": {
      if (state.status !== "submitting") {
        return state;
      }

      return {
        status: "error",
        question: state.question,
        message: event.message,
      };
    }

    case "RESET":
      return { status: "idle" };

    default:
      return assertNever(event);
  }
}

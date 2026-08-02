import type { ChatResponse, SourceItem } from "@/lib/types/chat";

export type ChatState =
  | { status: "idle" }
  | { status: "submitting"; question: string }
  | {
      status: "success";
      question: string;
      answer: string;
      sources: SourceItem[];
      /** Real, measured round-trip time for the `POST /chat` call (see
       * `hooks/useChatSession.ts`) — not mocked, unlike Confidence/Trust
       * Score elsewhere in the UI. */
      latencyMs: number;
    }
  | {
      status: "noSources";
      question: string;
      answer: string;
      /** Real, measured round-trip time for the `POST /chat` call — see
       * the "success" variant above. */
      latencyMs: number;
    }
  | { status: "error"; question: string; message: string };

export type ChatEvent =
  | { type: "SUBMIT_QUESTION"; question: string }
  | { type: "RESPONSE_RECEIVED"; response: ChatResponse; latencyMs: number }
  | { type: "REQUEST_FAILED"; message: string }
  | { type: "RESET" };

export const initialChatState: ChatState = { status: "idle" };

function assertNever(value: never): never {
  throw new Error(`Unhandled chat event: ${JSON.stringify(value)}`);
}

export function chatReducer(state: ChatState, event: ChatEvent): ChatState {
  switch (event.type) {
    case "SUBMIT_QUESTION":
      return { status: "submitting", question: event.question };

    case "RESPONSE_RECEIVED": {
      if (state.status !== "submitting") {
        return state;
      }

      const { question, answer, sources } = event.response;

      if (sources.length > 0) {
        return {
          status: "success",
          question,
          answer,
          sources,
          latencyMs: event.latencyMs,
        };
      }

      return {
        status: "noSources",
        question,
        answer,
        latencyMs: event.latencyMs,
      };
    }

    case "REQUEST_FAILED": {
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

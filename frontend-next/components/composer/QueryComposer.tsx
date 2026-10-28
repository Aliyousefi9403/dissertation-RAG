"use client";

import { useState, type FormEvent, type KeyboardEvent } from "react";

import { Button } from "@/components/ui/button";

const MIN_LENGTH = 1;
const MAX_LENGTH = 2000;

interface QueryComposerProps {
  onSubmit: (question: string) => void;
  disabled?: boolean;
  /** True only while the current question is in flight. */
  isSubmitting?: boolean;
  placeholder?: string;
}

export function QueryComposer({
  onSubmit,
  disabled = false,
  isSubmitting = false,
  placeholder = "Message AegisRAG...",
}: QueryComposerProps) {
  const [value, setValue] = useState("");

  const trimmed = value.trim();
  const isTooLong = trimmed.length > MAX_LENGTH;
  const isEmpty = trimmed.length < MIN_LENGTH;
  const canSubmit = !disabled && !isEmpty && !isTooLong;

  function submit() {
    if (!canSubmit) {
      return;
    }

    onSubmit(trimmed);
    setValue("");
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    submit();
  }

  // Enter submits; Shift+Enter inserts a newline. Only plain Enter is
  // intercepted (preventDefault + submit) — Shift+Enter is left entirely
  // to the textarea's native keydown behavior, which inserts "\n" itself.
  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  }

  const composerState = disabled ? (isSubmitting ? "submitting" : "disabled") : "idle";

  return (
    <div className="composer-wrapper">
      <form className="composer" data-state={composerState} onSubmit={handleSubmit}>
        <textarea
          value={value}
          onChange={(event) => setValue(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          rows={1}
          maxLength={MAX_LENGTH}
          disabled={disabled}
          aria-label="Ask AegisRAG a question"
        />

        <Button
          type="submit"
          variant="ghost"
          size="icon"
          disabled={!canSubmit}
          aria-label="Send question"
          className="composer-submit"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            aria-hidden="true"
            focusable="false"
          >
            <path
              d="M8 13V3M8 3L3.5 7.5M8 3l4.5 4.5"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </Button>
      </form>

      {isTooLong && (
        <p role="alert" className="composer-hint">
          Question is too long ({trimmed.length}/{MAX_LENGTH} characters).
        </p>
      )}
    </div>
  );
}

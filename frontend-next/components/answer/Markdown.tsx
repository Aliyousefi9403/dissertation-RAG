import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MarkdownProps {
  content: string;
}

/**
 * Shared Markdown renderer for backend-provided prose. Both the main
 * answer text and retrieved source excerpts arrive from the backend as
 * raw Markdown (headings, lists, emphasis, etc.) and must never be shown
 * as literal text — that renders `## Heading` as literal `##` characters
 * instead of styled headings. Centralised here so both call sites share
 * one `remark-gfm` config instead of duplicating it.
 *
 * Callers own layout/typography by wrapping this in an element with their
 * own class name (see `.answer-text` / `.source-row-content` in
 * globals.css) — this component intentionally renders no wrapper of its
 * own.
 */
export function Markdown({ content }: MarkdownProps) {
  return <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>;
}

"use client";

import { Fragment, type ReactNode } from "react";
import { BlockMath, InlineMath } from "react-katex";

/**
 * Render a single non-math segment with markdown bold and italic.
 * Bold is split first so that `*foo*` inside `**bar**` stays literal.
 * Both regexes require a closing delimiter — unclosed `**foo` falls
 * through as plain text, which is the behavior we want for AI replies
 * that get cut mid-stream.
 */
function parseMarkdown(text: string): ReactNode[] {
  const boldParts = text.split(/(\*\*[^*]+\*\*)/g);
  return boldParts.map((boldPart, i) => {
    if (boldPart.startsWith("**") && boldPart.endsWith("**")) {
      return <strong key={`b-${i}`}>{boldPart.slice(2, -2)}</strong>;
    }
    const italicParts = boldPart.split(/(\*[^*]+\*)/g);
    return (
      <Fragment key={`f-${i}`}>
        {italicParts.map((part, j) => {
          if (part.startsWith("*") && part.endsWith("*") && part.length >= 2) {
            return <em key={`i-${j}`}>{part.slice(1, -1)}</em>;
          }
          return part;
        })}
      </Fragment>
    );
  });
}

/**
 * Render text containing inline ($...$) and block ($$...$$) math segments
 * plus markdown bold (**) and italic (*). LaTeX is split first so dollar
 * signs never collide with markdown asterisks. Invalid LaTeX falls back
 * to the original raw text via react-katex's renderError prop.
 *
 * Limitations:
 * - Naive regex splits — no nested or escaped delimiters.
 * - Markdown supports only bold and italic. Code blocks, headings, lists
 *   and links are out of scope: the AI system prompt asks for short
 *   pedagogical replies that don't use them.
 */
export function KaTeXRenderer({ text }: { text: string }) {
  const parts = text.split(/(\$\$[^$]+\$\$|\$[^$]+\$)/g);

  return (
    <>
      {parts.map((part, i) => {
        if (part.startsWith("$$") && part.endsWith("$$")) {
          const math = part.slice(2, -2);
          return (
            <BlockMath
              key={i}
              math={math}
              renderError={() => <span>{part}</span>}
            />
          );
        }
        if (part.startsWith("$") && part.endsWith("$") && part.length >= 2) {
          const math = part.slice(1, -1);
          return (
            <InlineMath
              key={i}
              math={math}
              renderError={() => <span>{part}</span>}
            />
          );
        }
        if (part === "") return null;
        return <Fragment key={i}>{parseMarkdown(part)}</Fragment>;
      })}
    </>
  );
}

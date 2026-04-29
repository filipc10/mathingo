"use client";

import { BlockMath, InlineMath } from "react-katex";

/**
 * Render text containing inline ($...$) and block ($$...$$) math segments.
 * Splits on math delimiters and renders each part with the appropriate KaTeX
 * component. Invalid LaTeX falls back to the original raw text via react-katex's
 * renderError prop so a single bad prompt doesn't crash the page.
 *
 * Limitations:
 * - Naive regex split — does not support nested or escaped dollar signs.
 *   Our seed content sticks to simple inline math so this is fine.
 * - $$...$$ blocks are still rendered inline-flow; for true block layout
 *   wrap the renderer in a block-level container at the call site.
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
        return <span key={i}>{part}</span>;
      })}
    </>
  );
}

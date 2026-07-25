/**
 * MathEq.jsx — Lightweight KaTeX wrapper for rendering LaTeX math in React.
 * Usage:
 *   <MathBlock tex="\frac{dx}{dt} = -\nabla V" />   ← display (centered)
 *   <MathInline tex="\sigma" />                      ← inline
 */
import React from "react";
import katex from "katex";
import "katex/dist/katex.min.css";

function render(tex, displayMode) {
  try {
    return katex.renderToString(tex, {
      displayMode,
      throwOnError: false,
      trust: false,
      strict: false,
    });
  } catch {
    return `<span style="color:#f87171">[LaTeX error]</span>`;
  }
}

export function MathBlock({ tex, className = "" }) {
  return (
    <div
      className={"overflow-x-auto py-1 " + className}
      dangerouslySetInnerHTML={{ __html: render(tex, true) }}
    />
  );
}

export function MathInline({ tex }) {
  return (
    <span dangerouslySetInnerHTML={{ __html: render(tex, false) }} />
  );
}

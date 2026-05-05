"use client";

import { useEffect, useMemo, useState } from "react";
import { ArrowDown, ArrowUp } from "lucide-react";

import { cn } from "@/lib/utils";

import { KaTeXRenderer } from "./katex-renderer";

export type StepItem = {
  id: string;
  text: string;
};

export type StepOrderingPayload = {
  steps: StepItem[];
  instructions?: string | null;
};

type Phase = "answering" | "feedback";

// Mulberry32 + FNV-1a hash: tiny seeded PRNG. Seeded with the
// exercise id so the initial shuffle is stable across renders
// (no re-shuffling on state updates) but differs per exercise.
function mulberry32(seed: number) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function hashStringToInt(s: string): number {
  let hash = 2166136261;
  for (let i = 0; i < s.length; i++) {
    hash ^= s.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function seededShuffle<T>(items: T[], seed: string): T[] {
  const rand = mulberry32(hashStringToInt(seed));
  const out = [...items];
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

export function StepOrderingExercise({
  prompt,
  payload,
  exerciseId,
  value,
  onChange,
  phase = "answering",
  correctOrder,
}: {
  prompt: string;
  payload: StepOrderingPayload;
  exerciseId: string;
  value: string[] | null;
  onChange: (value: string[]) => void;
  phase?: Phase;
  correctOrder?: string[];
}) {
  const frozen = phase === "feedback";

  const initialOrder = useMemo(
    () => seededShuffle(payload.steps.map((s) => s.id), exerciseId),
    [payload.steps, exerciseId],
  );

  // The parent owns the final answer state; we seed it on mount with
  // the deterministic shuffle so submitting before any move sends the
  // visible order rather than null.
  useEffect(() => {
    if (!value || value.length !== payload.steps.length) {
      onChange(initialOrder);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [exerciseId]);

  const order =
    value && value.length === payload.steps.length ? value : initialOrder;

  const stepsById = useMemo(
    () => new Map(payload.steps.map((s) => [s.id, s])),
    [payload.steps],
  );

  function move(index: number, delta: number) {
    if (frozen) return;
    const target = index + delta;
    if (target < 0 || target >= order.length) return;
    const next = [...order];
    [next[index], next[target]] = [next[target], next[index]];
    onChange(next);
  }

  return (
    <div className="space-y-6">
      <div className="text-xl font-bold leading-relaxed">
        <KaTeXRenderer text={prompt} />
      </div>

      {payload.instructions && (
        <p className="text-sm font-medium text-muted-foreground">
          {payload.instructions}
        </p>
      )}

      <ol className="space-y-2">
        {order.map((id, index) => {
          const step = stepsById.get(id);
          if (!step) return null;

          const isAtCorrectPosition =
            frozen && correctOrder ? correctOrder[index] === id : null;

          return (
            <li
              key={id}
              className={cn(
                "flex items-center gap-3 rounded-xl border-2 p-3",
                isAtCorrectPosition === true && "border-accent bg-accent/5",
                isAtCorrectPosition === false &&
                  "border-destructive bg-destructive/5",
                isAtCorrectPosition === null && "border-border",
                frozen && "cursor-not-allowed",
              )}
            >
              <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-muted text-xs font-bold tabular-nums">
                {index + 1}.
              </span>
              <div className="flex-1 text-sm leading-relaxed">
                <KaTeXRenderer text={step.text} />
              </div>
              <div className="flex shrink-0 flex-col gap-1">
                <button
                  type="button"
                  onClick={() => move(index, -1)}
                  disabled={frozen || index === 0}
                  aria-label="Posunout nahoru"
                  className={cn(
                    "rounded-md border p-1 transition-colors",
                    !frozen &&
                      index !== 0 &&
                      "hover:border-primary hover:bg-primary/5",
                    (frozen || index === 0) && "opacity-40",
                  )}
                >
                  <ArrowUp className="size-4" />
                </button>
                <button
                  type="button"
                  onClick={() => move(index, 1)}
                  disabled={frozen || index === order.length - 1}
                  aria-label="Posunout dolů"
                  className={cn(
                    "rounded-md border p-1 transition-colors",
                    !frozen &&
                      index !== order.length - 1 &&
                      "hover:border-primary hover:bg-primary/5",
                    (frozen || index === order.length - 1) && "opacity-40",
                  )}
                >
                  <ArrowDown className="size-4" />
                </button>
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}

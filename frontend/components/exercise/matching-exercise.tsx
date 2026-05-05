"use client";

import { useState } from "react";

import { cn } from "@/lib/utils";

import { KaTeXRenderer } from "./katex-renderer";

export type MatchingPayload = {
  items: string[];
  categories: string[];
  instructions?: string | null;
};

type Phase = "answering" | "feedback";

type Assignments = Record<string, string>;

// Tap-tap pattern: select an unassigned item, then tap a category to
// place it. Tap an already-placed item to put it back to the pool.
// No HTML5 drag-and-drop — tap interaction works equally well on
// mobile and desktop, and stays accessible without focus tricks.
export function MatchingExercise({
  prompt,
  payload,
  value,
  onChange,
  phase = "answering",
  correctAnswer,
}: {
  prompt: string;
  payload: MatchingPayload;
  value: Assignments;
  onChange: (value: Assignments) => void;
  phase?: Phase;
  correctAnswer?: Assignments;
}) {
  const frozen = phase === "feedback";
  const [selectedItem, setSelectedItem] = useState<string | null>(null);

  function handleItemTap(item: string) {
    if (frozen) return;
    if (value[item]) {
      // Unassign — return to pool, clear any selection.
      const next = { ...value };
      delete next[item];
      onChange(next);
      setSelectedItem(null);
      return;
    }
    setSelectedItem(selectedItem === item ? null : item);
  }

  function handleCategoryTap(category: string) {
    if (frozen || !selectedItem) return;
    onChange({ ...value, [selectedItem]: category });
    setSelectedItem(null);
  }

  const unassignedItems = payload.items.filter((item) => !value[item]);

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

      <div className="space-y-2">
        <p className="text-xs font-bold uppercase tracking-wide text-muted-foreground">
          Nepřiřazené
        </p>
        <div className="flex flex-wrap gap-2">
          {unassignedItems.length === 0 ? (
            <span className="text-sm text-muted-foreground">
              Vše přiřazeno
            </span>
          ) : (
            unassignedItems.map((item) => {
              const isSelected = selectedItem === item;
              return (
                <button
                  key={item}
                  type="button"
                  onClick={() => handleItemTap(item)}
                  disabled={frozen}
                  className={cn(
                    "rounded-lg border-2 px-3 py-2 text-sm font-medium transition-all",
                    isSelected
                      ? "border-primary bg-primary/10"
                      : "border-border hover:border-primary/40 hover:bg-primary/5",
                    frozen && "cursor-not-allowed opacity-60",
                  )}
                >
                  <KaTeXRenderer text={item} />
                </button>
              );
            })
          )}
        </div>
      </div>

      <div className="space-y-3">
        {payload.categories.map((category) => {
          const assignedItems = payload.items.filter(
            (item) => value[item] === category,
          );
          const canDrop = !frozen && selectedItem !== null;

          return (
            <button
              key={category}
              type="button"
              onClick={() => handleCategoryTap(category)}
              disabled={frozen || !canDrop}
              className={cn(
                "w-full rounded-xl border-2 p-4 text-left transition-all",
                canDrop
                  ? "border-primary/40 bg-primary/5 hover:border-primary hover:bg-primary/10"
                  : "border-border",
                frozen && "cursor-not-allowed",
              )}
            >
              <div className="mb-2 text-base font-bold">
                <KaTeXRenderer text={category} />
              </div>
              <div className="flex flex-wrap gap-2">
                {assignedItems.length === 0 ? (
                  <span className="text-xs text-muted-foreground">
                    {canDrop ? "Klepnutím sem přiřaď" : "Prázdné"}
                  </span>
                ) : (
                  assignedItems.map((item) => {
                    const isCorrectInFrozen =
                      frozen && correctAnswer
                        ? correctAnswer[item] === category
                        : null;
                    return (
                      <span
                        key={item}
                        onClick={(e) => {
                          // In answering phase, clicking the chip removes
                          // the assignment so it can be re-placed.
                          if (frozen) return;
                          e.stopPropagation();
                          handleItemTap(item);
                        }}
                        className={cn(
                          "inline-flex cursor-pointer items-center rounded-md border px-2 py-1 text-xs font-medium transition-colors",
                          frozen && "cursor-not-allowed",
                          isCorrectInFrozen === true &&
                            "border-accent bg-accent/10 text-accent",
                          isCorrectInFrozen === false &&
                            "border-destructive bg-destructive/10 text-destructive",
                          isCorrectInFrozen === null &&
                            "border-primary bg-primary/10",
                        )}
                      >
                        <KaTeXRenderer text={item} />
                      </span>
                    );
                  })
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

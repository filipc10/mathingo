"use client";

import { cn } from "@/lib/utils";

import { KaTeXRenderer } from "./katex-renderer";

export type MultipleChoicePayload = {
  options: string[];
};

export function MultipleChoiceExercise({
  prompt,
  payload,
  selectedIndex,
  onSelect,
}: {
  prompt: string;
  payload: MultipleChoicePayload;
  selectedIndex: number | null;
  onSelect: (index: number) => void;
}) {
  return (
    <div className="space-y-6">
      <div className="text-xl font-bold leading-relaxed">
        <KaTeXRenderer text={prompt} />
      </div>
      <div className="space-y-3">
        {payload.options.map((option, idx) => {
          const isSelected = selectedIndex === idx;
          return (
            <button
              key={idx}
              type="button"
              onClick={() => onSelect(idx)}
              className={cn(
                "w-full rounded-xl border-2 px-4 py-4 text-left text-base transition-all",
                isSelected
                  ? "border-primary bg-primary/10 font-bold"
                  : "border-border font-medium hover:border-primary/40 hover:bg-primary/5",
              )}
            >
              <KaTeXRenderer text={option} />
            </button>
          );
        })}
      </div>
    </div>
  );
}

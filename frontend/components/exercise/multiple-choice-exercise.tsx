"use client";

import { cn } from "@/lib/utils";

import { KaTeXRenderer } from "./katex-renderer";

export type MultipleChoicePayload = {
  options: string[];
};

type Phase = "answering" | "feedback";

export function MultipleChoiceExercise({
  prompt,
  payload,
  selectedIndex,
  onSelect,
  phase = "answering",
  correctIndex,
}: {
  prompt: string;
  payload: MultipleChoicePayload;
  selectedIndex: number | null;
  onSelect: (index: number) => void;
  phase?: Phase;
  correctIndex?: number;
}) {
  const frozen = phase === "feedback";

  return (
    <div className="space-y-6">
      <div className="text-xl font-bold leading-relaxed">
        <KaTeXRenderer text={prompt} />
      </div>
      <div className="space-y-3">
        {payload.options.map((option, idx) => {
          const isSelected = selectedIndex === idx;
          const isCorrect = correctIndex === idx;

          // Four mutually-exclusive states in feedback phase:
          //   selected + correct      → strong green
          //   selected + incorrect    → strong red
          //   unselected + correct    → subtle green hint
          //   unselected + incorrect  → neutral disabled
          // In answering phase, only selected matters (primary blue).
          const className = cn(
            "w-full rounded-xl border-2 px-4 py-4 text-left text-base transition-all",
            !frozen && [
              isSelected
                ? "border-primary bg-primary/10 font-bold"
                : "border-border font-medium hover:border-primary/40 hover:bg-primary/5",
            ],
            frozen && [
              "cursor-not-allowed",
              isSelected && isCorrect && "border-accent bg-accent/10 font-bold",
              isSelected &&
                !isCorrect &&
                "border-destructive bg-destructive/10 font-bold",
              !isSelected &&
                isCorrect &&
                "border-accent/40 bg-accent/5 font-medium",
              !isSelected &&
                !isCorrect &&
                "border-border font-medium opacity-60",
            ],
          );

          return (
            <button
              key={idx}
              type="button"
              onClick={() => !frozen && onSelect(idx)}
              disabled={frozen}
              className={className}
            >
              <KaTeXRenderer text={option} />
            </button>
          );
        })}
      </div>
    </div>
  );
}

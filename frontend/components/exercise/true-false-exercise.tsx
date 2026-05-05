"use client";

import { Check, X } from "lucide-react";

import { cn } from "@/lib/utils";

import { KaTeXRenderer } from "./katex-renderer";

type Phase = "answering" | "feedback";

export function TrueFalseExercise({
  prompt,
  value,
  onSelect,
  phase = "answering",
  correctValue,
}: {
  prompt: string;
  value: boolean | null;
  onSelect: (value: boolean) => void;
  phase?: Phase;
  correctValue?: boolean;
}) {
  const frozen = phase === "feedback";

  return (
    <div className="space-y-6">
      <div className="text-xl font-bold leading-relaxed">
        <KaTeXRenderer text={prompt} />
      </div>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {([true, false] as const).map((option) => {
          const isSelected = value === option;
          const isCorrect = correctValue === option;

          const className = cn(
            "flex w-full items-center justify-center gap-2 rounded-xl border-2 px-4 py-5 text-lg font-bold transition-all",
            !frozen && [
              isSelected
                ? "border-primary bg-primary/10"
                : "border-border hover:border-primary/40 hover:bg-primary/5",
            ],
            frozen && [
              "cursor-not-allowed",
              isSelected && isCorrect && "border-accent bg-accent/10",
              isSelected && !isCorrect && "border-destructive bg-destructive/10",
              !isSelected && isCorrect && "border-accent/40 bg-accent/5",
              !isSelected && !isCorrect && "border-border opacity-60",
            ],
          );

          const Icon = option ? Check : X;
          const label = option ? "Pravda" : "Nepravda";

          return (
            <button
              key={String(option)}
              type="button"
              onClick={() => !frozen && onSelect(option)}
              disabled={frozen}
              className={className}
            >
              <Icon className="size-5" />
              {label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

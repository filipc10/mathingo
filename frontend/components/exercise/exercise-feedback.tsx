"use client";

import { CheckCircle2, Sparkles, XCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import { KaTeXRenderer } from "./katex-renderer";

import type { AnswerValue } from "@/app/lesson/[id]/actions";

export type ExerciseFeedbackData = {
  correct: boolean;
  user_answer: AnswerValue;
  correct_answer: AnswerValue;
  explanation: string | null;
};

export function ExerciseFeedback({
  feedback,
  onAskAi,
  showAskAi,
}: {
  feedback: ExerciseFeedbackData;
  onAskAi: () => void;
  showAskAi: boolean;
}) {
  const { correct, explanation } = feedback;

  return (
    <div className="space-y-4">
      <div
        className={cn(
          "flex items-start gap-3 rounded-xl border p-4",
          correct
            ? "border-accent/30 bg-accent/5"
            : "border-destructive/30 bg-destructive/5",
        )}
      >
        {correct ? (
          <CheckCircle2 className="size-7 shrink-0 text-accent" />
        ) : (
          <XCircle className="size-7 shrink-0 text-destructive" />
        )}
        <div className="flex-1 space-y-2">
          <p
            className={cn(
              "text-lg font-extrabold",
              correct ? "text-accent" : "text-destructive",
            )}
          >
            {correct ? "Správně!" : "Bohužel špatně."}
          </p>
          {explanation && (
            <div className="text-sm leading-relaxed text-muted-foreground">
              <KaTeXRenderer text={explanation} />
            </div>
          )}
        </div>
      </div>

      {showAskAi && (
        <Button
          variant="outline"
          size="lg"
          className="w-full"
          onClick={onAskAi}
        >
          <Sparkles className="size-4" />
          Chci to dovysvětlit
        </Button>
      )}
    </div>
  );
}

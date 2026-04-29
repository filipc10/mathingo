"use client";

import { CheckCircle2, Sparkles, XCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import { KaTeXRenderer } from "./katex-renderer";

export type ExerciseFeedbackData = {
  correct: boolean;
  user_answer: number | string;
  correct_answer: number | string;
  explanation: string | null;
};

export function ExerciseFeedback({
  feedback,
  onContinue,
  onAskAi,
  showAskAi,
  isLast,
}: {
  feedback: ExerciseFeedbackData;
  onContinue: () => void;
  onAskAi: () => void;
  showAskAi: boolean;
  isLast: boolean;
}) {
  const { correct, user_answer, correct_answer, explanation } = feedback;

  return (
    <div className="space-y-6">
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
          {!correct && (
            <div className="text-sm">
              <span className="text-muted-foreground">Tvoje odpověď: </span>
              <span className="font-bold">{String(user_answer)}</span>
              <span className="text-muted-foreground"> · Správně: </span>
              <span className="font-bold text-accent">
                {String(correct_answer)}
              </span>
            </div>
          )}
          {explanation && (
            <div className="text-sm leading-relaxed text-muted-foreground">
              <KaTeXRenderer text={explanation} />
            </div>
          )}
        </div>
      </div>

      <div className="space-y-3">
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
        <Button size="lg" className="w-full" onClick={onContinue}>
          {isLast ? "Dokončit lekci" : "Pokračovat"}
        </Button>
      </div>
    </div>
  );
}

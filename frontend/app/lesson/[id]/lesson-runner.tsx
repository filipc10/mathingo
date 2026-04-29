"use client";

import Link from "next/link";
import { useState, useTransition } from "react";
import { Loader2, X } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { ChatExplainPanel } from "@/components/exercise/chat-explain-panel";
import {
  ExerciseFeedback,
  type ExerciseFeedbackData,
} from "@/components/exercise/exercise-feedback";
import { LessonSummary } from "@/components/exercise/lesson-summary";
import {
  MultipleChoiceExercise,
  type MultipleChoicePayload,
} from "@/components/exercise/multiple-choice-exercise";
import { NumericExercise } from "@/components/exercise/numeric-exercise";

import {
  type AnswerSubmission,
  type SubmissionResponse,
  checkExerciseAnswer,
  submitLessonAnswers,
} from "./actions";

type Exercise = {
  id: string;
  order_index: number;
  exercise_type: "multiple_choice" | "numeric";
  prompt: string;
  payload: MultipleChoicePayload | Record<string, unknown>;
};

export type LessonData = {
  id: string;
  title: string;
  exercises: Exercise[];
};

// answering → checking → feedback → (next answering | summary)
type Phase =
  | { kind: "answering" }
  | { kind: "checking" }
  | { kind: "feedback"; data: ExerciseFeedbackData; askingAi: boolean }
  | { kind: "summary"; submission: SubmissionResponse };

export function LessonRunner({ lesson }: { lesson: LessonData }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number | string>>({});
  const [phase, setPhase] = useState<Phase>({ kind: "answering" });
  const [submitting, startSubmit] = useTransition();

  const total = lesson.exercises.length;
  const currentExercise = lesson.exercises[currentIndex];
  const currentAnswer = currentExercise
    ? answers[currentExercise.id]
    : undefined;
  const hasAnswer =
    currentAnswer !== undefined && currentAnswer !== null && currentAnswer !== "";
  const isLast = currentIndex === total - 1;

  function handleAnswer(value: number | string) {
    if (!currentExercise) return;
    setAnswers((prev) => ({ ...prev, [currentExercise.id]: value }));
  }

  async function handleCheck() {
    if (!currentExercise || !hasAnswer) return;
    setPhase({ kind: "checking" });
    const outcome = await checkExerciseAnswer(
      currentExercise.id,
      currentAnswer as number | string,
    );
    if (!outcome.ok) {
      toast.error(outcome.error);
      setPhase({ kind: "answering" });
      return;
    }
    setPhase({
      kind: "feedback",
      data: {
        correct: outcome.data.correct,
        user_answer: outcome.data.user_answer,
        correct_answer: outcome.data.correct_answer,
        explanation: outcome.data.explanation,
      },
      askingAi: false,
    });
  }

  function handleContinue() {
    if (!isLast) {
      setCurrentIndex(currentIndex + 1);
      setPhase({ kind: "answering" });
      return;
    }
    const payload: AnswerSubmission[] = lesson.exercises.map((ex) => ({
      exercise_id: ex.id,
      answer: answers[ex.id] as number | string,
    }));
    startSubmit(async () => {
      const outcome = await submitLessonAnswers(lesson.id, payload);
      if (!outcome.ok) {
        toast.error(outcome.error);
        return;
      }
      setPhase({ kind: "summary", submission: outcome.data });
    });
  }

  function handleAskAi() {
    if (phase.kind !== "feedback") return;
    setPhase({ ...phase, askingAi: true });
  }

  if (phase.kind === "summary") {
    return <LessonSummary submission={phase.submission} />;
  }

  const exercisePhase: "answering" | "feedback" =
    phase.kind === "feedback" ? "feedback" : "answering";
  const correctIndex =
    phase.kind === "feedback" &&
    currentExercise?.exercise_type === "multiple_choice" &&
    typeof phase.data.correct_answer === "number"
      ? phase.data.correct_answer
      : undefined;

  // Sticky bottom button label and disabled state depend on phase.
  const buttonLabel = (() => {
    if (phase.kind === "checking") return "Ověřuji…";
    if (phase.kind === "feedback") return isLast ? "Dokončit lekci" : "Pokračovat";
    return "Zkontrolovat";
  })();
  const buttonDisabled =
    phase.kind === "checking" ||
    submitting ||
    (phase.kind === "answering" && !hasAnswer);
  const buttonAction = phase.kind === "feedback" ? handleContinue : handleCheck;
  const buttonBusy = phase.kind === "checking" || submitting;

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-10 border-b bg-background/95 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-3xl items-center justify-between px-6">
          <span className="text-sm font-bold text-muted-foreground">
            Cvičení {currentIndex + 1} / {total}
          </span>
          <Link
            href="/learn"
            aria-label="Ukončit lekci"
            className="rounded-md p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            <X className="size-5" />
          </Link>
        </div>
      </header>

      <main className="mx-auto w-full max-w-xl flex-1 px-6 pb-32 pt-8">
        <div className="space-y-6">
          {currentExercise?.exercise_type === "multiple_choice" && (
            <MultipleChoiceExercise
              prompt={currentExercise.prompt}
              payload={currentExercise.payload as MultipleChoicePayload}
              selectedIndex={
                typeof currentAnswer === "number" ? currentAnswer : null
              }
              onSelect={handleAnswer}
              phase={exercisePhase}
              correctIndex={correctIndex}
            />
          )}
          {currentExercise?.exercise_type === "numeric" && (
            <NumericExercise
              prompt={currentExercise.prompt}
              value={
                typeof currentAnswer === "number" ? currentAnswer : null
              }
              onChange={(v) => handleAnswer(v ?? "")}
              phase={exercisePhase}
            />
          )}

          {phase.kind === "feedback" && currentExercise && (
            <>
              <ExerciseFeedback
                feedback={phase.data}
                onAskAi={handleAskAi}
                showAskAi={!phase.data.correct && !phase.askingAi}
              />
              {phase.askingAi && !phase.data.correct && (
                <ChatExplainPanel
                  exerciseId={currentExercise.id}
                  userAnswer={phase.data.user_answer}
                />
              )}
            </>
          )}
        </div>
      </main>

      <div className="sticky bottom-0 z-10 border-t bg-background/95 px-6 py-4 backdrop-blur">
        <div className="mx-auto max-w-xl">
          <Button
            size="lg"
            className="w-full"
            disabled={buttonDisabled}
            onClick={buttonAction}
          >
            {buttonBusy ? (
              <>
                <Loader2 className="size-4 animate-spin" />
                {buttonLabel}
              </>
            ) : (
              buttonLabel
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}

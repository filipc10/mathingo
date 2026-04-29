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
    // Last exercise — batch-submit so persistence (lesson_attempt, streak,
    // daily_activity) happens server-side and we get the high-level summary.
    const payload: AnswerSubmission[] = lesson.exercises.map((ex) => ({
      exercise_id: ex.id,
      answer: answers[ex.id] as number | string,
    }));
    startSubmit(async () => {
      const outcome = await submitLessonAnswers(lesson.id, payload);
      if (!outcome.ok) {
        toast.error(outcome.error);
        // Stay on feedback so the user can retry "Dokončit lekci"
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

      <main className="mx-auto flex w-full max-w-xl flex-1 flex-col px-6 py-8">
        <div className="flex-1 space-y-6">
          {currentExercise?.exercise_type === "multiple_choice" && (
            <MultipleChoiceExercise
              prompt={currentExercise.prompt}
              payload={currentExercise.payload as MultipleChoicePayload}
              selectedIndex={
                typeof currentAnswer === "number" ? currentAnswer : null
              }
              onSelect={handleAnswer}
            />
          )}
          {currentExercise?.exercise_type === "numeric" && (
            <NumericExercise
              prompt={currentExercise.prompt}
              value={
                typeof currentAnswer === "number" ? currentAnswer : null
              }
              onChange={(v) => handleAnswer(v ?? "")}
            />
          )}

          {phase.kind === "feedback" && currentExercise && (
            <>
              <ExerciseFeedback
                feedback={phase.data}
                onContinue={handleContinue}
                onAskAi={handleAskAi}
                showAskAi={!phase.data.correct && !phase.askingAi}
                isLast={isLast}
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

        {phase.kind !== "feedback" && (
          <div className="mt-8">
            <Button
              size="lg"
              className="w-full"
              disabled={!hasAnswer || phase.kind === "checking" || submitting}
              onClick={handleCheck}
            >
              {phase.kind === "checking" || submitting ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  Ověřuji…
                </>
              ) : (
                "Zkontrolovat"
              )}
            </Button>
          </div>
        )}
      </main>
    </div>
  );
}

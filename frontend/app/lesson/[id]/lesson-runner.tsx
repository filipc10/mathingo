"use client";

import Link from "next/link";
import { useState, useTransition } from "react";
import { Loader2, X } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  MultipleChoiceExercise,
  type MultipleChoicePayload,
} from "@/components/exercise/multiple-choice-exercise";
import { NumericExercise } from "@/components/exercise/numeric-exercise";

import {
  type AnswerSubmission,
  type SubmissionResponse,
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

type Phase = "answering" | "submitted";

export function LessonRunner({ lesson }: { lesson: LessonData }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number | string>>({});
  const [phase, setPhase] = useState<Phase>("answering");
  const [result, setResult] = useState<SubmissionResponse | null>(null);
  const [pending, startTransition] = useTransition();

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

  function handleNext() {
    if (currentIndex < total - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  }

  function handleSubmit() {
    const payload: AnswerSubmission[] = lesson.exercises.map((ex) => ({
      exercise_id: ex.id,
      answer: answers[ex.id] as number | string,
    }));
    startTransition(async () => {
      const outcome = await submitLessonAnswers(lesson.id, payload);
      if (!outcome.ok) {
        toast.error(outcome.error);
        return;
      }
      setResult(outcome.data);
      setPhase("submitted");
    });
  }

  if (phase === "submitted" && result) {
    return (
      <div className="mx-auto max-w-xl px-6 py-12 text-center">
        <h1 className="mb-4">
          {result.score.correct_count} / {result.score.total_count}
        </h1>
        <p className="mb-8 text-muted-foreground">
          Dotazy jsou vyhodnocené. (Detailní rozbor přijde v dalším commitu.)
        </p>
        <Button asChild size="lg" className="w-full">
          <Link href="/learn">Zpět na cestu</Link>
        </Button>
      </div>
    );
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
        <div className="flex-1">
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
        </div>

        <div className="mt-8">
          {!isLast ? (
            <Button
              size="lg"
              className="w-full"
              disabled={!hasAnswer}
              onClick={handleNext}
            >
              Pokračovat
            </Button>
          ) : (
            <Button
              size="lg"
              className="w-full"
              disabled={!hasAnswer || pending}
              onClick={handleSubmit}
            >
              {pending ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  Odesílám…
                </>
              ) : (
                "Dokončit"
              )}
            </Button>
          )}
        </div>
      </main>
    </div>
  );
}

"use client";

import Link from "next/link";
import { useState, useTransition } from "react";
import { Loader2, X } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { ChatExplainPanel } from "@/components/exercise/chat-explain-panel";
import { ClozeExercise, type ClozePayload } from "@/components/exercise/cloze-exercise";
import {
  ExerciseFeedback,
  type ExerciseFeedbackData,
} from "@/components/exercise/exercise-feedback";
import { LessonSummary } from "@/components/exercise/lesson-summary";
import {
  MatchingExercise,
  type MatchingPayload,
} from "@/components/exercise/matching-exercise";
import {
  MultipleChoiceExercise,
  type MultipleChoicePayload,
} from "@/components/exercise/multiple-choice-exercise";
import { NumericExercise } from "@/components/exercise/numeric-exercise";
import {
  StepOrderingExercise,
  type StepOrderingPayload,
} from "@/components/exercise/step-ordering-exercise";
import { TrueFalseExercise } from "@/components/exercise/true-false-exercise";

import {
  type AnswerSubmission,
  type AnswerValue,
  type SubmissionResponse,
  checkExerciseAnswer,
  submitLessonAnswers,
} from "./actions";

type ExerciseType =
  | "multiple_choice"
  | "numeric"
  | "true_false"
  | "cloze"
  | "matching"
  | "step_ordering";

type Exercise = {
  id: string;
  order_index: number;
  exercise_type: ExerciseType;
  prompt: string;
  payload: Record<string, unknown>;
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

function hasCompleteAnswer(exercise: Exercise, answer: AnswerValue | undefined): boolean {
  if (answer === undefined || answer === null) return false;
  switch (exercise.exercise_type) {
    case "multiple_choice":
      return typeof answer === "number";
    case "numeric":
      return typeof answer === "number";
    case "true_false":
      return typeof answer === "boolean";
    case "cloze":
      return typeof answer === "string" && answer.trim().length > 0;
    case "matching": {
      if (
        typeof answer !== "object" ||
        Array.isArray(answer) ||
        typeof answer === "boolean"
      ) {
        return false;
      }
      const items = (exercise.payload as MatchingPayload).items ?? [];
      return Object.keys(answer).length === items.length;
    }
    case "step_ordering":
      return Array.isArray(answer) && answer.length > 0;
  }
}

export function LessonRunner({ lesson }: { lesson: LessonData }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, AnswerValue>>({});
  const [phase, setPhase] = useState<Phase>({ kind: "answering" });
  const [submitting, startSubmit] = useTransition();

  const total = lesson.exercises.length;
  const currentExercise = lesson.exercises[currentIndex];
  const currentAnswer = currentExercise ? answers[currentExercise.id] : undefined;
  const hasAnswer = currentExercise
    ? hasCompleteAnswer(currentExercise, currentAnswer)
    : false;
  const isLast = currentIndex === total - 1;

  function handleAnswer(value: AnswerValue) {
    if (!currentExercise) return;
    setAnswers((prev) => ({ ...prev, [currentExercise.id]: value }));
  }

  async function handleCheck() {
    if (!currentExercise || !hasAnswer) return;
    setPhase({ kind: "checking" });
    const outcome = await checkExerciseAnswer(
      currentExercise.id,
      currentAnswer as AnswerValue,
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
      answer: answers[ex.id] as AnswerValue,
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

  const correctAnswer =
    phase.kind === "feedback" ? phase.data.correct_answer : undefined;

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
              correctIndex={
                typeof correctAnswer === "number" ? correctAnswer : undefined
              }
            />
          )}
          {currentExercise?.exercise_type === "numeric" && (
            <NumericExercise
              prompt={currentExercise.prompt}
              value={typeof currentAnswer === "number" ? currentAnswer : null}
              onChange={(v) => handleAnswer(v ?? "")}
              phase={exercisePhase}
            />
          )}
          {currentExercise?.exercise_type === "cloze" && (
            <ClozeExercise
              prompt={currentExercise.prompt}
              payload={currentExercise.payload as ClozePayload}
              value={typeof currentAnswer === "string" ? currentAnswer : ""}
              onChange={handleAnswer}
              phase={exercisePhase}
            />
          )}
          {currentExercise?.exercise_type === "true_false" && (
            <TrueFalseExercise
              prompt={currentExercise.prompt}
              value={typeof currentAnswer === "boolean" ? currentAnswer : null}
              onSelect={handleAnswer}
              phase={exercisePhase}
              correctValue={
                typeof correctAnswer === "boolean" ? correctAnswer : undefined
              }
            />
          )}
          {currentExercise?.exercise_type === "matching" && (
            <MatchingExercise
              prompt={currentExercise.prompt}
              payload={currentExercise.payload as MatchingPayload}
              value={
                currentAnswer &&
                typeof currentAnswer === "object" &&
                !Array.isArray(currentAnswer) &&
                typeof currentAnswer !== "boolean"
                  ? (currentAnswer as Record<string, string>)
                  : {}
              }
              onChange={handleAnswer}
              phase={exercisePhase}
              correctAnswer={
                correctAnswer &&
                typeof correctAnswer === "object" &&
                !Array.isArray(correctAnswer)
                  ? (correctAnswer as Record<string, string>)
                  : undefined
              }
            />
          )}
          {currentExercise?.exercise_type === "step_ordering" && (
            <StepOrderingExercise
              prompt={currentExercise.prompt}
              payload={currentExercise.payload as StepOrderingPayload}
              exerciseId={currentExercise.id}
              value={Array.isArray(currentAnswer) ? currentAnswer : null}
              onChange={handleAnswer}
              phase={exercisePhase}
              correctOrder={
                Array.isArray(correctAnswer) ? correctAnswer : undefined
              }
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

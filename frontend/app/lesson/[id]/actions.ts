"use server";

import { cookies } from "next/headers";

import { apiUrl } from "@/lib/api";

// Discriminated by exercise type at the call site:
//   multiple_choice → number       (option index)
//   numeric         → number
//   true_false      → boolean
//   cloze           → string
//   matching        → Record<string, string>
//   step_ordering   → string[]
export type AnswerValue =
  | number
  | string
  | boolean
  | Record<string, string>
  | string[];

export type AnswerSubmission = {
  exercise_id: string;
  answer: AnswerValue;
};

export type ExerciseResult = {
  exercise_id: string;
  correct: boolean;
  user_answer: AnswerValue;
  correct_answer: AnswerValue;
  explanation: string | null;
};

export type SubmissionResponse = {
  lesson_id: string;
  results: ExerciseResult[];
  score: {
    correct_count: number;
    total_count: number;
    all_correct: boolean;
  };
  progress: {
    is_completed: boolean;
    xp_earned: number;
    user_streak: number;
    user_xp_today: number;
  };
};

export type ExerciseCheckResult = {
  exercise_id: string;
  correct: boolean;
  user_answer: AnswerValue;
  correct_answer: AnswerValue;
  explanation: string | null;
};

export async function checkExerciseAnswer(
  exerciseId: string,
  answer: AnswerValue,
): Promise<
  { ok: true; data: ExerciseCheckResult } | { ok: false; error: string }
> {
  const cookieStore = await cookies();
  const session = cookieStore.get("mathingo_session");
  if (!session) {
    return { ok: false, error: "Tvá relace vypršela. Přihlas se prosím znovu." };
  }

  const res = await fetch(apiUrl(`/exercises/${exerciseId}/check`), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      cookie: `mathingo_session=${session.value}`,
    },
    body: JSON.stringify({ answer }),
    cache: "no-store",
  });

  if (!res.ok) {
    return { ok: false, error: "Nepovedlo se ověřit odpověď. Zkus to znovu." };
  }

  const data = (await res.json()) as ExerciseCheckResult;
  return { ok: true, data };
}

export async function submitLessonAnswers(
  lessonId: string,
  answers: AnswerSubmission[],
): Promise<{ ok: true; data: SubmissionResponse } | { ok: false; error: string }> {
  const cookieStore = await cookies();
  const session = cookieStore.get("mathingo_session");
  if (!session) {
    return { ok: false, error: "Tvá relace vypršela. Přihlas se prosím znovu." };
  }

  const res = await fetch(apiUrl(`/lessons/${lessonId}/submit`), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      cookie: `mathingo_session=${session.value}`,
    },
    body: JSON.stringify({ answers }),
    cache: "no-store",
  });

  if (!res.ok) {
    return { ok: false, error: "Nepovedlo se odeslat odpovědi. Zkus to znovu." };
  }

  const data = (await res.json()) as SubmissionResponse;
  return { ok: true, data };
}

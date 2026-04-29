"use server";

import { cookies } from "next/headers";

import { apiUrl } from "@/lib/api";

export type AnswerSubmission = {
  exercise_id: string;
  answer: number | string;
};

export type ExerciseResult = {
  exercise_id: string;
  correct: boolean;
  user_answer: number | string;
  correct_answer: number | string;
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

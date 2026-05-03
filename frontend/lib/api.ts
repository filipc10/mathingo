import { cookies } from "next/headers";

const isServer = typeof window === "undefined";

const baseUrl = isServer
  ? process.env.BACKEND_INTERNAL_URL ?? "http://backend:8000"
  : process.env.NEXT_PUBLIC_API_URL ?? "/api";

export function apiUrl(path: string): string {
  return `${baseUrl}${path.startsWith("/") ? path : `/${path}`}`;
}

export type LessonStats = {
  lesson_id: string;
  lesson_title: string;
  total_exercises: number;
  attempted: number;
  correct_attempts: number;
  total_attempts: number;
  winrate: number;
  is_completed: boolean;
  best_score: number;
};

export type SectionStats = {
  section_id: string;
  section_title: string;
  total_exercises: number;
  attempted: number;
  correct_attempts: number;
  total_attempts: number;
  winrate: number;
  lessons: LessonStats[];
};

export type TypeStats = {
  exercise_type: string;
  total_attempts: number;
  correct_attempts: number;
  winrate: number;
};

export type UserStats = {
  total_xp: number;
  current_streak: number;
  longest_streak: number;
  lessons_completed: number;
  total_exercise_attempts: number;
  overall_winrate: number;
  sections: SectionStats[];
  by_type: TypeStats[];
  last_active_date: string | null;
};

// Server-side fetch helper. Reads the session cookie from the request and
// forwards it to the backend so /users/me/stats authenticates correctly.
// Returns null on auth failure (401) so callers can redirect to /signin.
export async function fetchUserStats(): Promise<UserStats | null> {
  const cookieStore = await cookies();
  const session = cookieStore.get("mathingo_session");
  if (!session) return null;

  const res = await fetch(apiUrl("/users/me/stats"), {
    headers: { cookie: `mathingo_session=${session.value}` },
    cache: "no-store",
  });

  if (!res.ok) return null;
  return (await res.json()) as UserStats;
}

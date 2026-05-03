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

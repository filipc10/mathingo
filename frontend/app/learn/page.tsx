import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { PathStone } from "@/components/learn/path-stone";
import { TopBar } from "@/components/learn/top-bar";
import { getCurrentUser } from "@/lib/auth";
import { vocative } from "@/lib/vocative";

const COURSE_CODE = "4MM101";
const STONE_OFFSETS = [0, 56, 80, 56, 0, -56, -80];

type LessonSummary = {
  id: string;
  order_index: number;
  title: string;
  description: string | null;
  xp_reward: number;
};

type SectionWithLessons = {
  id: string;
  order_index: number;
  title: string;
  description: string | null;
  lessons: LessonSummary[];
};

type CourseStructure = {
  id: string;
  code: string;
  title: string;
  sections: SectionWithLessons[];
};

type CourseProgress = {
  course_id: string;
  completed_lesson_ids: string[];
};

async function fetchPublic<T>(path: string): Promise<T | null> {
  const base = process.env.BACKEND_INTERNAL_URL ?? "http://backend:8000";
  const res = await fetch(`${base}${path}`, { cache: "no-store" });
  if (!res.ok) return null;
  return (await res.json()) as T;
}

async function fetchAuth<T>(path: string, cookieValue: string): Promise<T | null> {
  const base = process.env.BACKEND_INTERNAL_URL ?? "http://backend:8000";
  const res = await fetch(`${base}${path}`, {
    headers: { cookie: `mathingo_session=${cookieValue}` },
    cache: "no-store",
  });
  if (!res.ok) return null;
  return (await res.json()) as T;
}

type StoneState = "completed" | "available" | "locked";

function computeLessonState(
  index: number,
  sectionLessons: LessonSummary[],
  completedIds: Set<string>,
): StoneState {
  const lesson = sectionLessons[index];
  if (completedIds.has(lesson.id)) return "completed";
  if (index === 0) return "available";
  // Available if every previous lesson in this section is completed
  for (let i = 0; i < index; i++) {
    if (!completedIds.has(sectionLessons[i].id)) return "locked";
  }
  return "available";
}

export default async function LearnPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/signin");
  if (user.first_name === "" || user.display_name === "") {
    redirect("/onboarding");
  }

  const cookieStore = await cookies();
  const session = cookieStore.get("mathingo_session");
  if (!session) redirect("/signin");

  const [structure, progress] = await Promise.all([
    fetchPublic<CourseStructure>(`/courses/${COURSE_CODE}/structure`),
    fetchAuth<CourseProgress>(
      `/courses/${COURSE_CODE}/progress`,
      session.value,
    ),
  ]);

  if (!structure) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-muted-foreground">Kurz se nepodařilo načíst.</p>
      </div>
    );
  }

  const completedIds = new Set(progress?.completed_lesson_ids ?? []);

  return (
    <div className="min-h-screen bg-background">
      <TopBar
        streak={user.streak}
        xpToday={user.xp_today}
        dailyXpGoal={user.daily_xp_goal}
        displayName={user.display_name}
        avatarVariant={user.avatar_variant}
        avatarPalette={user.avatar_palette}
      />

      <main className="mx-auto max-w-3xl px-6 py-12">
        <div className="mb-12 text-center">
          <h1 className="mb-2">Vítej, {vocative(user.first_name)}!</h1>
          <p className="font-medium text-muted-foreground">
            Tvoje cesta lekcemi začíná zde.
          </p>
        </div>

        {structure.sections.map((section) => (
          <section key={section.id} className="mb-16">
            <div className="mb-8 text-center">
              <h2 className="text-2xl">{section.title}</h2>
              {section.description && (
                <p className="mt-2 text-sm font-medium text-muted-foreground">
                  {section.description}
                </p>
              )}
            </div>

            <div className="flex flex-col items-center gap-8">
              {section.lessons.map((lesson, idx) => {
                const status = computeLessonState(
                  idx,
                  section.lessons,
                  completedIds,
                );
                const offset =
                  STONE_OFFSETS[idx % STONE_OFFSETS.length] ?? 0;
                return (
                  <PathStone
                    key={lesson.id}
                    status={status}
                    label={lesson.order_index}
                    offset={offset}
                    lessonId={lesson.id}
                  />
                );
              })}
            </div>
          </section>
        ))}
      </main>
    </div>
  );
}

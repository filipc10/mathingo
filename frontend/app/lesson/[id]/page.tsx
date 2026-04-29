import { notFound, redirect } from "next/navigation";

import { getCurrentUser } from "@/lib/auth";

import { LessonRunner, type LessonData } from "./lesson-runner";

async function fetchLesson(lessonId: string): Promise<LessonData | null> {
  const base = process.env.BACKEND_INTERNAL_URL ?? "http://backend:8000";
  const res = await fetch(`${base}/lessons/${lessonId}`, { cache: "no-store" });
  if (!res.ok) return null;
  return (await res.json()) as LessonData;
}

export default async function LessonPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const user = await getCurrentUser();
  if (!user) redirect("/signin");
  if (user.first_name === "" || user.display_name === "") redirect("/onboarding");

  const lesson = await fetchLesson(id);
  if (!lesson) notFound();

  return <LessonRunner lesson={lesson} />;
}

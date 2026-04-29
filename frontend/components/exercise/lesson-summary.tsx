"use client";

import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import type { SubmissionResponse } from "@/app/lesson/[id]/actions";

export function LessonSummary({
  submission,
}: {
  submission: SubmissionResponse;
}) {
  const { score, progress } = submission;

  const xpMessage = (() => {
    if (progress.xp_earned > 0) {
      return `+${progress.xp_earned} XP`;
    }
    if (progress.is_completed) {
      return "Lekci jsi zvládl/a! Bez XP — už jsi ji dokončil/a dříve.";
    }
    return "Pro získání XP potřebuješ aspoň 80 % správně.";
  })();

  const xpClassName = cn(
    "text-lg font-bold",
    progress.xp_earned > 0
      ? "text-accent"
      : "text-muted-foreground font-medium",
  );

  return (
    <div className="mx-auto flex min-h-screen max-w-xl flex-col justify-center px-6 py-12">
      <div className="space-y-6 text-center">
        <h1 className="text-6xl font-extrabold tracking-tight text-primary">
          {score.correct_count} / {score.total_count}
        </h1>
        <p className={xpClassName}>{xpMessage}</p>
        <p className="text-sm font-medium text-muted-foreground">
          🔥 {progress.user_streak} dní · {progress.user_xp_today} XP dnes
        </p>
        <Link
          href="/learn"
          className={cn(buttonVariants({ size: "lg" }), "mt-6 w-full")}
        >
          Zpět na cestu
        </Link>
      </div>
    </div>
  );
}

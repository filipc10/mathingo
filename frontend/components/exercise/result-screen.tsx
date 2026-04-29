"use client";

import Link from "next/link";
import { CheckCircle2, XCircle } from "lucide-react";

import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import type { SubmissionResponse } from "@/app/lesson/[id]/actions";

import { KaTeXRenderer } from "./katex-renderer";

type Exercise = {
  id: string;
  prompt: string;
};

export function ResultScreen({
  submission,
  exercises,
}: {
  submission: SubmissionResponse;
  exercises: Exercise[];
}) {
  const { score, progress } = submission;
  const promptById = new Map(exercises.map((ex) => [ex.id, ex.prompt]));

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
    <div className="mx-auto max-w-xl space-y-8 px-6 py-12">
      <div className="space-y-3 text-center">
        <h1 className="text-5xl font-extrabold tracking-tight text-primary">
          {score.correct_count} / {score.total_count}
        </h1>
        <p className={xpClassName}>{xpMessage}</p>
        <p className="text-sm font-medium text-muted-foreground">
          🔥 {progress.user_streak} dní · {progress.user_xp_today} XP dnes
        </p>
      </div>

      <div className="space-y-4">
        {submission.results.map((r) => {
          const prompt = promptById.get(r.exercise_id) ?? "";
          return (
            <div
              key={r.exercise_id}
              className="space-y-3 rounded-xl border bg-card p-4"
            >
              <div className="flex items-start gap-3">
                {r.correct ? (
                  <CheckCircle2 className="size-6 shrink-0 text-accent" />
                ) : (
                  <XCircle className="size-6 shrink-0 text-destructive" />
                )}
                <div className="flex-1 space-y-2">
                  <div className="font-medium leading-relaxed">
                    <KaTeXRenderer text={prompt} />
                  </div>
                  {!r.correct && (
                    <div className="text-sm">
                      <span className="text-muted-foreground">
                        Tvoje odpověď:{" "}
                      </span>
                      <span className="font-bold">{String(r.user_answer)}</span>
                      <span className="text-muted-foreground">
                        {" · Správně: "}
                      </span>
                      <span className="font-bold text-accent">
                        {String(r.correct_answer)}
                      </span>
                    </div>
                  )}
                  {r.explanation && (
                    <div className="text-sm leading-relaxed text-muted-foreground">
                      <KaTeXRenderer text={r.explanation} />
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <Link
        href="/learn"
        className={cn(buttonVariants({ size: "lg" }), "w-full")}
      >
        Zpět na cestu
      </Link>
    </div>
  );
}

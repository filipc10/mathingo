"use client";

import { useState } from "react";
import { CheckCircle, ChevronDown, ChevronRight, Circle } from "lucide-react";

import { Card } from "@/components/ui/card";
import type { LessonStats, SectionStats } from "@/lib/api";

export function SectionBreakdown({ sections }: { sections: SectionStats[] }) {
  if (sections.length === 0) {
    return (
      <p className="text-center text-muted-foreground">
        Žádné téma zatím není k dispozici.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {sections.map((section) => (
        <SectionRow key={section.section_id} section={section} />
      ))}
    </div>
  );
}

function SectionRow({ section }: { section: SectionStats }) {
  const [expanded, setExpanded] = useState(false);
  const winrate = section.total_attempts
    ? section.correct_attempts / section.total_attempts
    : 0;

  return (
    <Card className="!p-0">
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="flex w-full items-center gap-3 px-4 py-4 text-left transition-colors hover:bg-muted/50"
        aria-expanded={expanded}
      >
        {expanded ? (
          <ChevronDown className="size-5 shrink-0 text-muted-foreground" />
        ) : (
          <ChevronRight className="size-5 shrink-0 text-muted-foreground" />
        )}
        <div className="min-w-0 flex-1">
          <div className="truncate font-bold">{section.section_title}</div>
          <div className="truncate text-sm text-muted-foreground">
            {section.attempted} / {section.total_exercises} cvičení
            {section.total_attempts > 0 && (
              <> · {(winrate * 100).toFixed(0)}% úspěšnost</>
            )}
          </div>
        </div>
        {section.total_attempts > 0 && (
          <div className="hidden h-2 w-24 shrink-0 overflow-hidden rounded-full bg-muted sm:block">
            <div
              className="h-full bg-accent"
              style={{ width: `${winrate * 100}%` }}
            />
          </div>
        )}
      </button>

      {expanded && (
        <div className="space-y-1 border-t border-border px-4 py-3">
          {section.lessons.map((lesson) => (
            <LessonRow key={lesson.lesson_id} lesson={lesson} />
          ))}
        </div>
      )}
    </Card>
  );
}

function LessonRow({ lesson }: { lesson: LessonStats }) {
  const winrate = lesson.total_attempts
    ? lesson.correct_attempts / lesson.total_attempts
    : 0;

  return (
    <div className="flex items-start gap-3 py-1.5">
      {lesson.is_completed ? (
        <CheckCircle className="mt-0.5 size-5 shrink-0 text-accent" />
      ) : (
        <Circle className="mt-0.5 size-5 shrink-0 text-muted-foreground" />
      )}
      <div className="min-w-0 flex-1">
        <div className="truncate text-sm font-medium">
          {lesson.lesson_title}
        </div>
        {lesson.total_attempts > 0 ? (
          <div className="text-xs text-muted-foreground">
            {lesson.attempted} / {lesson.total_exercises} cvičení ·{" "}
            {(winrate * 100).toFixed(0)}% · nejlepší skóre{" "}
            {(lesson.best_score * 100).toFixed(0)}%
          </div>
        ) : (
          <div className="text-xs text-muted-foreground italic">
            Zatím nezkoušeno
          </div>
        )}
      </div>
    </div>
  );
}

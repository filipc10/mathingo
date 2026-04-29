import Link from "next/link";
import { Check, Lock } from "lucide-react";

import { cn } from "@/lib/utils";

type Status = "available" | "locked" | "completed";

const baseClasses =
  "flex size-20 items-center justify-center rounded-full text-2xl font-extrabold shadow-md transition-transform";

export function PathStone({
  status,
  label,
  offset,
  lessonId,
}: {
  status: Status;
  label: string | number;
  offset: number;
  lessonId?: string;
}) {
  const inner = (
    <span
      style={{ transform: `translateX(${offset}px)` }}
      className={cn(
        baseClasses,
        status === "available" &&
          "bg-primary text-primary-foreground hover:scale-110 active:scale-95",
        status === "locked" &&
          "cursor-not-allowed bg-muted text-muted-foreground",
        status === "completed" &&
          "bg-accent text-accent-foreground hover:scale-110 active:scale-95",
      )}
    >
      {status === "locked" && <Lock className="size-7" />}
      {status === "completed" && <Check className="size-9" strokeWidth={3} />}
      {status === "available" && label}
    </span>
  );

  if ((status === "available" || status === "completed") && lessonId) {
    return (
      <Link
        href={`/lesson/${lessonId}`}
        aria-label={`Lekce ${label}`}
        className="inline-block"
      >
        {inner}
      </Link>
    );
  }

  return (
    <button
      type="button"
      disabled
      aria-label={`Lekce ${label} — zamčeno`}
      className="inline-block"
    >
      {inner}
    </button>
  );
}

import { Lock } from "lucide-react";

import { cn } from "@/lib/utils";

type Status = "available" | "locked" | "completed";

export function PathStone({
  status,
  label,
  offset,
}: {
  status: Status;
  label: string | number;
  offset: number;
}) {
  const isLocked = status === "locked";

  return (
    <button
      type="button"
      disabled={isLocked}
      style={{ transform: `translateX(${offset}px)` }}
      aria-label={isLocked ? `Lekce ${label} — zamčeno` : `Lekce ${label}`}
      className={cn(
        "flex size-20 items-center justify-center rounded-full text-2xl font-extrabold shadow-md transition-transform",
        status === "available" &&
          "cursor-pointer bg-primary text-primary-foreground hover:scale-110 active:scale-95",
        status === "locked" &&
          "cursor-not-allowed bg-muted text-muted-foreground",
        status === "completed" && "bg-accent text-accent-foreground",
      )}
    >
      {isLocked ? <Lock className="size-7" /> : label}
    </button>
  );
}

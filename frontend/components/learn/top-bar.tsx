import Link from "next/link";
import { Trophy } from "lucide-react";

export function TopBar({
  streak,
  xpToday,
  dailyXpGoal,
}: {
  streak: number;
  xpToday: number;
  dailyXpGoal: number;
}) {
  return (
    <header className="sticky top-0 z-10 border-b bg-background/95 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-3xl items-center justify-between px-6">
        <Link
          href="/learn"
          className="text-xl font-extrabold text-primary"
        >
          Mathingo
        </Link>
        <div className="flex items-center gap-3 text-sm font-bold">
          <Link
            href="/leaderboard"
            aria-label="Žebříček"
            className="text-muted-foreground transition-colors hover:text-primary"
          >
            <Trophy className="size-5" />
          </Link>
          <span aria-hidden className="text-muted-foreground">
            ·
          </span>
          <span className="flex items-center gap-1.5">
            <span aria-hidden>🔥</span>
            <span>{streak} dní</span>
          </span>
          <span aria-hidden className="text-muted-foreground">
            ·
          </span>
          <span className="text-muted-foreground">
            {xpToday} / {dailyXpGoal} XP
          </span>
        </div>
      </div>
    </header>
  );
}

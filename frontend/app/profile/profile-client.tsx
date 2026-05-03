"use client";

import { Award, BookOpen, Flame, Pencil, Target } from "lucide-react";

import { TopBar } from "@/components/learn/top-bar";
import { UserAvatar } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { UserStats } from "@/lib/api";
import type { CurrentUser } from "@/lib/auth";

import { SectionBreakdown } from "./section-breakdown";
import { TypeStatsBlock } from "./type-stats";

type Props = {
  user: CurrentUser;
  initialStats: UserStats;
};

export function ProfileClient({ user, initialStats }: Props) {
  const stats = initialStats;

  return (
    <div className="min-h-screen bg-background">
      <TopBar
        streak={user.streak}
        xpToday={user.xp_today}
        dailyXpGoal={user.daily_xp_goal}
      />

      <main className="mx-auto max-w-3xl space-y-8 px-4 py-8 sm:px-6 sm:py-12">
        <header className="flex flex-wrap items-center gap-4 sm:gap-6">
          <UserAvatar
            name={user.display_name}
            variant={user.avatar_variant}
            palette={user.avatar_palette}
            size={96}
          />
          <div className="min-w-0 flex-1">
            <h1 className="truncate text-2xl font-extrabold tracking-tight sm:text-3xl">
              {user.first_name}
            </h1>
            <p className="truncate text-muted-foreground">
              @{user.display_name}
            </p>
          </div>
          <Button variant="outline" size="lg" disabled>
            <Pencil className="size-4" />
            Upravit
          </Button>
        </header>

        <div className="grid grid-cols-2 gap-3 md:grid-cols-4 md:gap-4">
          <StatCard
            icon={<Award className="size-5" />}
            label="Celkem XP"
            value={stats.total_xp.toString()}
          />
          <StatCard
            icon={<Flame className="size-5" />}
            label="Aktuální série"
            value={`${stats.current_streak} dní`}
          />
          <StatCard
            icon={<Target className="size-5" />}
            label="Nejdelší série"
            value={`${stats.longest_streak} dní`}
          />
          <StatCard
            icon={<BookOpen className="size-5" />}
            label="Dokončené lekce"
            value={stats.lessons_completed.toString()}
          />
        </div>

        <Card>
          <CardContent className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold">Celková úspěšnost</span>
              <span className="text-2xl font-extrabold">
                {(stats.overall_winrate * 100).toFixed(0)}%
              </span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-muted">
              <div
                className="h-full bg-accent transition-all"
                style={{ width: `${stats.overall_winrate * 100}%` }}
              />
            </div>
            <p className="text-sm text-muted-foreground">
              {stats.total_exercise_attempts} pokusů celkem
            </p>
          </CardContent>
        </Card>

        <section className="space-y-4">
          <h2 className="text-xl font-extrabold tracking-tight">
            Podle typu cvičení
          </h2>
          <TypeStatsBlock data={stats.by_type} />
        </section>

        <section className="space-y-4">
          <h2 className="text-xl font-extrabold tracking-tight">
            Podle témat
          </h2>
          <SectionBreakdown sections={stats.sections} />
        </section>
      </main>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <Card>
      <CardContent className="space-y-1">
        <div className="text-muted-foreground">{icon}</div>
        <div className="text-2xl font-extrabold">{value}</div>
        <div className="text-sm text-muted-foreground">{label}</div>
      </CardContent>
    </Card>
  );
}

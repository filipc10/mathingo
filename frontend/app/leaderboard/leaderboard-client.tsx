"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";

import { UserAvatar } from "@/components/ui/avatar";
import { Tabs, TabsList, TabsPanel, TabsTab } from "@/components/ui/tabs";
import { apiUrl } from "@/lib/api";
import { cn } from "@/lib/utils";

export type LeaderboardEntry = {
  rank: number;
  user_id: string;
  display_name: string;
  xp: number;
  streak: number;
  is_current_user: boolean;
};

export type LeaderboardResponse = {
  entries: LeaderboardEntry[];
  user_rank: number | null;
  user_xp: number | null;
  total_users: number;
};

type Tab = "weekly" | "total";

const RANK_BADGES: Record<number, string> = { 1: "🥇", 2: "🥈", 3: "🥉" };

export function LeaderboardClient({
  initialWeekly,
}: {
  initialWeekly: LeaderboardResponse | null;
}) {
  const [tab, setTab] = useState<Tab>("weekly");
  const [weekly] = useState<LeaderboardResponse | null>(initialWeekly);
  const [total, setTotal] = useState<LeaderboardResponse | null>(null);
  const [loadingTotal, setLoadingTotal] = useState(false);

  async function loadTotal() {
    if (total || loadingTotal) return;
    setLoadingTotal(true);
    try {
      const res = await fetch(apiUrl("/leaderboard/total"), {
        credentials: "include",
        cache: "no-store",
      });
      if (res.ok) {
        setTotal((await res.json()) as LeaderboardResponse);
      }
    } finally {
      setLoadingTotal(false);
    }
  }

  return (
    <Tabs
      value={tab}
      onValueChange={(v) => {
        const next = v as Tab;
        setTab(next);
        if (next === "total") loadTotal();
      }}
    >
      <TabsList className="grid w-full grid-cols-2">
        <TabsTab value="weekly">Tento týden</TabsTab>
        <TabsTab value="total">Celkem</TabsTab>
      </TabsList>
      <TabsPanel value="weekly">
        <LeaderboardList data={weekly} loading={false} />
      </TabsPanel>
      <TabsPanel value="total">
        <LeaderboardList data={total} loading={loadingTotal} />
      </TabsPanel>
    </Tabs>
  );
}

function LeaderboardList({
  data,
  loading,
}: {
  data: LeaderboardResponse | null;
  loading: boolean;
}) {
  if (loading || data === null) {
    return (
      <div className="flex justify-center py-12 text-muted-foreground">
        <Loader2 className="size-6 animate-spin" />
      </div>
    );
  }

  if (data.entries.length === 0) {
    return (
      <p className="py-12 text-center text-sm font-medium text-muted-foreground">
        Zatím nikdo nemá XP. Buď první!
      </p>
    );
  }

  const showOwnPosition =
    data.user_rank !== null && data.user_xp !== null && data.user_rank > 10;

  return (
    <div className="space-y-2">
      {data.entries.map((entry) => (
        <LeaderboardRow key={entry.user_id} entry={entry} />
      ))}
      {showOwnPosition && (
        <div className="mt-8 border-t pt-6">
          <p className="mb-2 text-center text-xs font-bold uppercase tracking-wide text-muted-foreground">
            Tvoje pozice
          </p>
          <div className="flex items-center gap-4 rounded-xl border-2 border-primary bg-primary/10 p-4">
            <div className="w-10 text-center text-2xl font-extrabold">
              {data.user_rank}.
            </div>
            <UserAvatar name={"current-user"} size={48} />
            <div className="flex-1">
              <div className="font-bold">Ty</div>
            </div>
            <div className="text-xl font-extrabold tabular-nums">
              {data.user_xp} XP
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function LeaderboardRow({ entry }: { entry: LeaderboardEntry }) {
  const badge = RANK_BADGES[entry.rank];
  return (
    <div
      className={cn(
        "flex items-center gap-4 rounded-xl border-2 p-4 transition-colors",
        entry.is_current_user
          ? "border-primary bg-primary/10"
          : "border-border bg-card",
      )}
    >
      <div className="w-10 text-center text-2xl font-extrabold">
        {badge ?? `${entry.rank}.`}
      </div>
      <UserAvatar name={entry.display_name} size={40} />
      <div className="flex-1">
        <div className="font-bold">
          {entry.is_current_user ? `${entry.display_name} (ty)` : entry.display_name}
        </div>
        <div className="text-sm font-medium text-muted-foreground">
          🔥 {entry.streak} dní
        </div>
      </div>
      <div className="text-xl font-extrabold tabular-nums">
        {entry.xp} XP
      </div>
    </div>
  );
}

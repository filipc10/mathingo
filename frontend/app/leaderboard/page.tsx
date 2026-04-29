import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { TopBar } from "@/components/learn/top-bar";
import { getCurrentUser } from "@/lib/auth";

import { LeaderboardClient, type LeaderboardResponse } from "./leaderboard-client";

async function fetchAuth<T>(
  path: string,
  cookieValue: string,
): Promise<T | null> {
  const base = process.env.BACKEND_INTERNAL_URL ?? "http://backend:8000";
  const res = await fetch(`${base}${path}`, {
    headers: { cookie: `mathingo_session=${cookieValue}` },
    cache: "no-store",
  });
  if (!res.ok) return null;
  return (await res.json()) as T;
}

export default async function LeaderboardPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/signin");
  if (user.first_name === "" || user.display_name === "") {
    redirect("/onboarding");
  }

  const cookieStore = await cookies();
  const session = cookieStore.get("mathingo_session");
  if (!session) redirect("/signin");

  const weekly = await fetchAuth<LeaderboardResponse>(
    "/leaderboard/weekly",
    session.value,
  );

  return (
    <div className="min-h-screen bg-background">
      <TopBar
        streak={user.streak}
        xpToday={user.xp_today}
        dailyXpGoal={user.daily_xp_goal}
      />
      <main className="mx-auto max-w-2xl px-6 py-10">
        <h1 className="mb-8 text-center text-3xl font-extrabold tracking-tight">
          🏆 Žebříček
        </h1>
        <LeaderboardClient initialWeekly={weekly} />
      </main>
    </div>
  );
}

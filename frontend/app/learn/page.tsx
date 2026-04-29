import Image from "next/image";
import Link from "next/link";
import { redirect } from "next/navigation";

import { PathStone } from "@/components/learn/path-stone";
import { getCurrentUser } from "@/lib/auth";
import { vocative } from "@/lib/vocative";

const STONES = [
  { i: 1, status: "available" as const, offset: 0 },
  { i: 2, status: "locked" as const, offset: 56 },
  { i: 3, status: "locked" as const, offset: 80 },
  { i: 4, status: "locked" as const, offset: 56 },
  { i: 5, status: "locked" as const, offset: 0 },
  { i: 6, status: "locked" as const, offset: -56 },
  { i: 7, status: "locked" as const, offset: -80 },
];

export default async function LearnPage() {
  const user = await getCurrentUser();
  if (!user) {
    redirect("/signin");
  }
  if (user.first_name === "" || user.display_name === "") {
    redirect("/onboarding");
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-10 border-b bg-background/95 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-3xl items-center justify-between px-6">
          <Link href="/learn" aria-label="Mathingo">
            <Image
              src="/logo.png"
              alt="Mathingo"
              width={1200}
              height={675}
              priority
              className="h-8 w-auto"
            />
          </Link>
          <div className="flex items-center gap-3 text-sm font-bold">
            <span className="flex items-center gap-1.5">
              <span aria-hidden>🔥</span>
              <span>0 dní</span>
            </span>
            <span aria-hidden className="text-muted-foreground">
              ·
            </span>
            <span className="text-muted-foreground">
              0 / {user.daily_xp_goal} XP
            </span>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-6 py-12">
        <div className="mb-12 text-center">
          <h1 className="mb-2">Vítej, {vocative(user.first_name)}!</h1>
          <p className="font-medium text-muted-foreground">
            Tvoje cesta lekcemi začíná zde.
          </p>
        </div>

        <div className="flex flex-col items-center gap-8">
          {STONES.map((s) => (
            <PathStone
              key={s.i}
              status={s.status}
              label={s.i}
              offset={s.offset}
            />
          ))}
        </div>
      </main>
    </div>
  );
}

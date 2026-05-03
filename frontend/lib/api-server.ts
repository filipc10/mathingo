import { cookies } from "next/headers";

import { apiUrl, type UserStats } from "./api";

// Server-only fetch helpers. Lives in its own module so that lib/api.ts
// stays safe to import from client components (a top-level `next/headers`
// import in a shared module breaks the client bundle).
export async function fetchUserStats(): Promise<UserStats | null> {
  const cookieStore = await cookies();
  const session = cookieStore.get("mathingo_session");
  if (!session) return null;

  const res = await fetch(apiUrl("/users/me/stats"), {
    headers: { cookie: `mathingo_session=${session.value}` },
    cache: "no-store",
  });

  if (!res.ok) return null;
  return (await res.json()) as UserStats;
}

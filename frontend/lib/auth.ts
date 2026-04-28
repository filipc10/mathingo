import { cookies } from "next/headers";
import { apiUrl } from "./api";

export type CurrentUser = {
  id: string;
  email: string;
  display_name: string;
  daily_xp_goal: number;
};

export async function getCurrentUser(): Promise<CurrentUser | null> {
  const cookieStore = await cookies();
  const session = cookieStore.get("mathingo_session");
  if (!session) return null;

  const res = await fetch(apiUrl("/auth/me"), {
    headers: { cookie: `mathingo_session=${session.value}` },
    cache: "no-store",
  });

  if (!res.ok) return null;
  return (await res.json()) as CurrentUser;
}

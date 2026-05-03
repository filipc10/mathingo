import { redirect } from "next/navigation";

import { fetchUserStats } from "@/lib/api";
import { getCurrentUser } from "@/lib/auth";

import { ProfileClient } from "./profile-client";

export default async function ProfilePage() {
  const user = await getCurrentUser();
  if (!user) redirect("/signin");
  if (user.first_name === "" || user.display_name === "") {
    redirect("/onboarding");
  }

  const stats = await fetchUserStats();
  if (!stats) redirect("/signin");

  return <ProfileClient user={user} initialStats={stats} />;
}

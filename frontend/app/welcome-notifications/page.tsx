import { redirect } from "next/navigation";

import { getCurrentUser } from "@/lib/auth";

import { WelcomeNotificationsClient } from "./welcome-client";

export default async function WelcomeNotificationsPage() {
  const user = await getCurrentUser();
  if (!user) redirect("/signin");
  // Reachable only after onboarding; if a user lands here without a
  // profile, send them back to finish it. Same guard as /learn uses.
  if (!user.first_name || !user.display_name) redirect("/onboarding");

  return <WelcomeNotificationsClient userFirstName={user.first_name} />;
}

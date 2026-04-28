"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { apiUrl } from "@/lib/api";

const ALLOWED_GOALS = new Set([10, 20, 40]);

export async function onboardingAction(
  formData: FormData,
): Promise<{ error: string } | undefined> {
  const displayName = formData.get("display_name");
  const goalRaw = formData.get("daily_xp_goal");

  if (
    typeof displayName !== "string" ||
    displayName.length < 3 ||
    displayName.length > 40
  ) {
    return { error: "Přezdívka musí mít 3 až 40 znaků." };
  }

  const goal = Number(goalRaw);
  if (!ALLOWED_GOALS.has(goal)) {
    return { error: "Vyber jeden z denních cílů." };
  }

  const cookieStore = await cookies();
  const session = cookieStore.get("mathingo_session");
  if (!session) {
    return { error: "Tvá relace vypršela. Přihlaš se prosím znovu." };
  }

  const res = await fetch(apiUrl("/auth/onboarding"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      cookie: `mathingo_session=${session.value}`,
    },
    body: JSON.stringify({ display_name: displayName, daily_xp_goal: goal }),
    cache: "no-store",
  });

  if (res.status === 409) {
    return { error: "Tato přezdívka už je obsazená. Vyber si jinou." };
  }
  if (!res.ok) {
    return { error: "Něco se nepovedlo. Zkus to znovu." };
  }

  redirect("/learn");
}

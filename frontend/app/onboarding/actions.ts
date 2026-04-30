"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { apiUrl } from "@/lib/api";
import { AVATAR_PALETTES, AVATAR_VARIANTS } from "@/lib/avatars";

const ALLOWED_GOALS = new Set([10, 20, 40]);
const ALLOWED_VARIANTS = new Set<string>(AVATAR_VARIANTS);
const ALLOWED_PALETTES = new Set<string>(Object.keys(AVATAR_PALETTES));

export async function onboardingAction(
  formData: FormData,
): Promise<{ error: string } | undefined> {
  const firstNameRaw = formData.get("first_name");
  const displayNameRaw = formData.get("display_name");
  const goalRaw = formData.get("daily_xp_goal");
  const variantRaw = formData.get("avatar_variant");
  const paletteRaw = formData.get("avatar_palette");

  const firstName =
    typeof firstNameRaw === "string" ? firstNameRaw.trim() : "";
  const displayName =
    typeof displayNameRaw === "string" ? displayNameRaw.trim() : "";

  if (firstName.length < 1 || firstName.length > 40) {
    return { error: "Zadej své jméno (1 až 40 znaků)." };
  }
  if (displayName.length < 3 || displayName.length > 30) {
    return { error: "Přezdívka musí mít 3 až 30 znaků." };
  }

  const goal = Number(goalRaw);
  if (!ALLOWED_GOALS.has(goal)) {
    return { error: "Vyber jeden z denních cílů." };
  }

  const variant = typeof variantRaw === "string" ? variantRaw : "";
  const palette = typeof paletteRaw === "string" ? paletteRaw : "";
  if (!ALLOWED_VARIANTS.has(variant) || !ALLOWED_PALETTES.has(palette)) {
    return { error: "Vyber si avatar." };
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
    body: JSON.stringify({
      first_name: firstName,
      display_name: displayName,
      daily_xp_goal: goal,
      avatar_variant: variant,
      avatar_palette: palette,
    }),
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

"use server";

import { redirect } from "next/navigation";
import { apiUrl } from "@/lib/api";

export async function signinAction(
  formData: FormData,
): Promise<{ error: string } | undefined> {
  const email = formData.get("email");
  if (typeof email !== "string" || email.length === 0) {
    return { error: "Zadej platný e-mail." };
  }

  const res = await fetch(apiUrl("/auth/signin"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
    cache: "no-store",
  });

  if (!res.ok) {
    return { error: "Něco se nepovedlo. Zkus to znovu." };
  }

  redirect("/check-email");
}

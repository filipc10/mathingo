import { redirect } from "next/navigation";

import { getCurrentUser } from "@/lib/auth";

export default async function LearnPage() {
  const user = await getCurrentUser();
  if (!user) {
    redirect("/signin");
  }
  if (user.display_name === "") {
    redirect("/onboarding");
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-white px-6 py-12 text-center dark:bg-neutral-950">
      <div>
        <h1 className="text-4xl font-bold tracking-tight">Mathingo</h1>
        <p className="mt-4 text-lg text-muted-foreground">
          Vítej, {user.display_name}! Tady bude tvoje cesta lekcemi.
        </p>
      </div>
    </main>
  );
}

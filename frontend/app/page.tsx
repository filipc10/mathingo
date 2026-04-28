import Link from "next/link";
import { redirect } from "next/navigation";

import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { getCurrentUser } from "@/lib/auth";

export default async function Home() {
  const user = await getCurrentUser();
  if (user) {
    redirect(user.display_name === "" ? "/onboarding" : "/learn");
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-white px-6 text-center dark:bg-neutral-950">
      <h1 className="text-5xl font-bold tracking-tight text-neutral-900 dark:text-neutral-50 sm:text-6xl">
        Mathingo
      </h1>
      <p className="mt-4 max-w-md text-lg text-neutral-600 dark:text-neutral-400">
        Procvičování vysokoškolské matematiky po pár minutách denně.
      </p>
      <Link
        href="/signin"
        className={cn(buttonVariants({ size: "lg" }), "mt-8")}
      >
        Začít
      </Link>
    </main>
  );
}

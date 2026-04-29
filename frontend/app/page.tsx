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
    <main className="flex min-h-screen flex-col items-center justify-center bg-background px-6 py-16 text-center">
      <div className="animate-in fade-in slide-in-from-bottom-2 flex flex-col items-center gap-8 duration-500">
        <h1 className="text-6xl text-primary md:text-8xl">Mathingo</h1>
        <p className="max-w-md text-lg leading-relaxed font-medium text-muted-foreground md:text-xl">
          Procvičuj matematiku, jak jsi zvyklý/á procvičovat jazyky.
        </p>
        <Link
          href="/signin"
          className={cn(buttonVariants({ size: "lg" }), "mt-4 px-8 text-lg")}
        >
          Začít
        </Link>
      </div>
    </main>
  );
}

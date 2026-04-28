import { redirect } from "next/navigation";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { getCurrentUser } from "@/lib/auth";

import { OnboardingForm } from "./onboarding-form";

export default async function OnboardingPage() {
  const user = await getCurrentUser();
  if (!user) {
    redirect("/signin");
  }
  if (user.display_name !== "") {
    redirect("/learn");
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-white px-6 py-12 dark:bg-neutral-950">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Vítej v Mathingo</CardTitle>
          <CardDescription>
            Pověz nám něco o sobě, ať můžeme nastavit cestu lekcemi.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <OnboardingForm />
        </CardContent>
      </Card>
    </main>
  );
}

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
  if (user.first_name !== "" && user.display_name !== "") {
    redirect("/learn");
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-6 py-12">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <CardTitle className="text-3xl font-extrabold tracking-tight">
            Vítej v Mathingo
          </CardTitle>
          <CardDescription className="text-base">
            Pověz nám něco o sobě, ať můžeme nastavit cestu lekcemi.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <OnboardingForm initialDisplayName={user.display_name} />
        </CardContent>
      </Card>
    </main>
  );
}

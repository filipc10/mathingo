import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import { SigninForm } from "./signin-form";

const ERROR_MESSAGES: Record<string, string> = {
  invalid_or_expired:
    "Tvůj odkaz byl neplatný nebo už vypršel. Pošli si nový níže.",
};

export default async function SignInPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const params = await searchParams;
  const errorMessage = params.error ? ERROR_MESSAGES[params.error] : null;

  return (
    <main className="flex min-h-screen items-center justify-center bg-white px-6 dark:bg-neutral-950">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Přihlásit se do Mathingo</CardTitle>
          <CardDescription>
            Pošleme ti odkaz, kterým se přihlásíš.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4">
          {errorMessage && (
            <p
              role="alert"
              className="text-sm text-red-600 dark:text-red-400"
            >
              {errorMessage}
            </p>
          )}
          <SigninForm />
        </CardContent>
      </Card>
    </main>
  );
}

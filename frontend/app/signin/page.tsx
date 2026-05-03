import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import { SigninForm } from "./signin-form";

const ERROR_MESSAGES: Record<string, string> = {
  invalid: "Tvůj odkaz není platný. Pošli si nový níže.",
  expired: "Tvůj odkaz už vypršel. Pošli si nový níže.",
  already_used: "Tento odkaz už byl použit. Pošli si nový níže.",
  network: "Něco se nepovedlo. Zkus to prosím znovu.",
  unknown: "Něco se nepovedlo. Zkus to prosím znovu.",
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
    <main className="flex min-h-screen items-center justify-center bg-background px-6 py-12">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-2xl font-extrabold tracking-tight">
            Přihlas se
          </CardTitle>
          <CardDescription className="text-base">
            Pošleme ti přihlašovací odkaz na e-mail.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-5">
          {errorMessage && (
            <p
              role="alert"
              className="rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm font-medium text-destructive"
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

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Mail } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export function ClickClient({ token }: { token: string }) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  async function handleSignIn() {
    setLoading(true);

    try {
      const response = await fetch("/api/auth/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token }),
      });

      if (!response.ok) {
        const reason =
          response.status === 404
            ? "invalid"
            : response.status === 410
              ? "already_used"
              : "unknown";
        router.replace(`/signin?error=${reason}`);
        return;
      }

      const data = (await response.json()) as { redirect_to: string };
      router.replace(data.redirect_to);
    } catch {
      router.replace("/signin?error=network");
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4 py-12">
      <Card className="w-full max-w-md">
        <CardContent className="space-y-6 text-center">
          <div className="flex justify-center">
            <div className="flex size-16 items-center justify-center rounded-full bg-primary/10">
              <Mail className="size-8 text-primary" />
            </div>
          </div>

          <div className="space-y-2">
            <h1 className="text-2xl font-extrabold tracking-tight">
              Téměř hotovo!
            </h1>
            <p className="text-muted-foreground">
              Klikni níže pro dokončení přihlášení.
            </p>
          </div>

          <Button
            onClick={handleSignIn}
            disabled={loading}
            className="w-full"
            size="lg"
          >
            {loading ? "Přihlašuji…" : "Přihlásit se"}
          </Button>
        </CardContent>
      </Card>
    </main>
  );
}

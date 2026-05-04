"use client";

import { useState } from "react";
import { LogOut } from "lucide-react";

import { Button } from "@/components/ui/button";

export function SignOutButton() {
  const [pending, setPending] = useState(false);

  async function signOut() {
    setPending(true);
    try {
      await fetch("/api/auth/signout", {
        method: "POST",
        credentials: "same-origin",
      });
    } catch {
      // Even if the network call fails the user clearly wants out —
      // hard-redirect to /signin and let the next request 401 itself
      // back to a clean state.
    }
    window.location.href = "/signin";
  }

  return (
    <Button
      variant="outline"
      size="lg"
      onClick={signOut}
      disabled={pending}
      className="w-full"
    >
      <LogOut className="size-4" />
      {pending ? "Odhlašuji…" : "Odhlásit se"}
    </Button>
  );
}

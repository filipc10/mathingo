"use client";

import { useTransition } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import { signinAction } from "./actions";

export function SigninForm() {
  const [pending, startTransition] = useTransition();

  function onSubmit(formData: FormData) {
    startTransition(async () => {
      const result = await signinAction(formData);
      if (result?.error) {
        toast.error(result.error);
      }
    });
  }

  return (
    <form action={onSubmit} className="grid gap-4">
      <div className="grid gap-2">
        <Label htmlFor="email">Tvůj e-mail</Label>
        <Input
          id="email"
          name="email"
          type="email"
          autoComplete="email"
          required
          placeholder="ty@example.cz"
        />
      </div>
      <Button type="submit" disabled={pending}>
        {pending ? "Odesílám…" : "Poslat odkaz"}
      </Button>
    </form>
  );
}

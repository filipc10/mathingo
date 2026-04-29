"use client";

import { useTransition } from "react";
import { Loader2 } from "lucide-react";
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
        <Label htmlFor="email" className="font-bold">
          Tvůj e-mail
        </Label>
        <Input
          id="email"
          name="email"
          type="email"
          autoComplete="email"
          required
          placeholder="tvuj@email.cz"
        />
      </div>
      <Button type="submit" size="lg" disabled={pending} className="mt-2 w-full">
        {pending ? (
          <>
            <Loader2 className="size-4 animate-spin" />
            Odesílám…
          </>
        ) : (
          "Poslat odkaz"
        )}
      </Button>
    </form>
  );
}

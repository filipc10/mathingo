"use client";

import { useTransition } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";

import { onboardingAction } from "./actions";

const GOALS = [
  { value: "10", label: "Lehký", subtitle: "10 XP / den" },
  { value: "20", label: "Střední", subtitle: "20 XP / den" },
  { value: "40", label: "Náročný", subtitle: "40 XP / den" },
];

export function OnboardingForm() {
  const [pending, startTransition] = useTransition();

  function onSubmit(formData: FormData) {
    startTransition(async () => {
      const result = await onboardingAction(formData);
      if (result?.error) {
        toast.error(result.error);
      }
    });
  }

  return (
    <form action={onSubmit} className="grid gap-6">
      <div className="grid gap-2">
        <Label htmlFor="display_name">Přezdívka</Label>
        <Input
          id="display_name"
          name="display_name"
          minLength={3}
          maxLength={40}
          required
          autoComplete="nickname"
        />
        <p className="text-xs text-muted-foreground">
          3 až 40 znaků. Uvidí ji ostatní v žebříčku.
        </p>
      </div>

      <div className="grid gap-2">
        <Label>Denní cíl XP</Label>
        <RadioGroup
          name="daily_xp_goal"
          defaultValue="20"
          className="grid gap-2"
        >
          {GOALS.map((g) => (
            <label
              key={g.value}
              htmlFor={`goal-${g.value}`}
              className="flex cursor-pointer items-center gap-3 rounded-md border px-4 py-3 hover:bg-accent"
            >
              <RadioGroupItem value={g.value} id={`goal-${g.value}`} />
              <span className="flex-1">
                <span className="font-medium">{g.label}</span>
                <span className="ml-2 text-sm text-muted-foreground">
                  {g.subtitle}
                </span>
              </span>
            </label>
          ))}
        </RadioGroup>
      </div>

      <Button type="submit" disabled={pending}>
        {pending ? "Ukládám…" : "Pokračovat"}
      </Button>
    </form>
  );
}

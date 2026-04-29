"use client";

import { useTransition } from "react";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { cn } from "@/lib/utils";

import { onboardingAction } from "./actions";

const GOALS = [
  {
    value: "10",
    label: "Lehký",
    subtitle: "5 minut denně",
    xp: "10 XP",
  },
  {
    value: "20",
    label: "Střední",
    subtitle: "10 minut denně",
    xp: "20 XP",
  },
  {
    value: "40",
    label: "Náročný",
    subtitle: "15+ minut denně",
    xp: "40 XP",
  },
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
        <Label htmlFor="display_name" className="font-bold">
          Přezdívka
        </Label>
        <Input
          id="display_name"
          name="display_name"
          minLength={3}
          maxLength={40}
          required
          autoComplete="nickname"
        />
        <p className="text-xs font-medium text-muted-foreground">
          3 až 40 znaků. Uvidí ji ostatní v žebříčku.
        </p>
      </div>

      <div className="grid gap-3">
        <Label className="font-bold">Denní cíl XP</Label>
        <RadioGroup
          name="daily_xp_goal"
          defaultValue="20"
          className="grid gap-2"
        >
          {GOALS.map((g) => (
            <label
              key={g.value}
              htmlFor={`goal-${g.value}`}
              className={cn(
                "flex cursor-pointer items-center gap-4 rounded-xl border-2 p-4 transition-all",
                "hover:border-primary/40 hover:bg-primary/5",
                "has-[[data-checked]]:border-primary has-[[data-checked]]:bg-primary/5",
              )}
            >
              <RadioGroupItem value={g.value} id={`goal-${g.value}`} />
              <div className="flex flex-1 flex-col gap-0.5">
                <span className="font-bold">{g.label}</span>
                <span className="text-sm text-muted-foreground">
                  {g.subtitle}
                </span>
              </div>
              <span className="font-extrabold tabular-nums text-foreground">
                {g.xp}
              </span>
            </label>
          ))}
        </RadioGroup>
      </div>

      <Button type="submit" size="lg" disabled={pending} className="mt-2 w-full">
        {pending ? (
          <>
            <Loader2 className="size-4 animate-spin" />
            Ukládám…
          </>
        ) : (
          "Pokračovat"
        )}
      </Button>
    </form>
  );
}

"use client";

import { useState, useTransition } from "react";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

import { UserAvatar } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  AVATAR_PALETTES,
  AVATAR_VARIANTS,
  AvatarPalette,
  AvatarVariant,
  DEFAULT_AVATAR_PALETTE,
  DEFAULT_AVATAR_VARIANT,
} from "@/lib/avatars";
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

const PALETTE_LABELS: Record<AvatarPalette, string> = {
  blue: "Modrá",
  green: "Zelená",
  purple: "Fialová",
  sunset: "Západ slunce",
  mono: "Mono",
};

export function OnboardingForm({
  initialDisplayName = "",
}: {
  initialDisplayName?: string;
}) {
  const [pending, startTransition] = useTransition();
  const [displayName, setDisplayName] = useState(initialDisplayName);
  const [variant, setVariant] = useState<AvatarVariant>(
    DEFAULT_AVATAR_VARIANT,
  );
  const [palette, setPalette] = useState<AvatarPalette>(
    DEFAULT_AVATAR_PALETTE,
  );

  function onSubmit(formData: FormData) {
    formData.set("avatar_variant", variant);
    formData.set("avatar_palette", palette);
    startTransition(async () => {
      const result = await onboardingAction(formData);
      if (result?.error) {
        toast.error(result.error);
      }
    });
  }

  const previewName = displayName.trim() || "Mathingo";

  return (
    <form action={onSubmit} className="grid gap-6">
      <div className="grid gap-2">
        <Label htmlFor="first_name" className="font-bold">
          Jak ti říkat?
        </Label>
        <Input
          id="first_name"
          name="first_name"
          minLength={1}
          maxLength={40}
          required
          autoComplete="given-name"
          autoFocus
        />
        <p className="text-xs font-medium text-muted-foreground">
          Např. Filip nebo Anna. Použijeme to při oslovení.
        </p>
      </div>

      <div className="grid gap-2">
        <Label htmlFor="display_name" className="font-bold">
          Přezdívka
        </Label>
        <Input
          id="display_name"
          name="display_name"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          minLength={3}
          maxLength={30}
          required
          autoComplete="nickname"
        />
        <p className="text-xs font-medium text-muted-foreground">
          3 až 30 znaků. Uvidí ji ostatní v žebříčku.
        </p>
      </div>

      <div className="grid gap-3">
        <Label className="font-bold">Avatar</Label>
        <div className="flex items-center gap-4 rounded-xl border-2 p-4">
          <UserAvatar
            name={previewName}
            size={64}
            variant={variant}
            palette={palette}
          />
          <p className="text-sm text-muted-foreground">
            Náhled tvého avataru. Vybírá se podle přezdívky a barev.
          </p>
        </div>

        <div className="grid grid-cols-3 gap-2 sm:grid-cols-6">
          {AVATAR_VARIANTS.map((v) => (
            <button
              type="button"
              key={v}
              onClick={() => setVariant(v)}
              aria-pressed={variant === v}
              className={cn(
                "flex items-center justify-center rounded-xl border-2 p-2 transition-all",
                "hover:border-primary/40 hover:bg-primary/5",
                variant === v && "border-primary bg-primary/10",
              )}
            >
              <UserAvatar
                name={previewName}
                size={48}
                variant={v}
                palette={palette}
              />
            </button>
          ))}
        </div>

        <div className="grid grid-cols-5 gap-2">
          {(Object.keys(AVATAR_PALETTES) as AvatarPalette[]).map((p) => (
            <button
              type="button"
              key={p}
              onClick={() => setPalette(p)}
              aria-pressed={palette === p}
              aria-label={PALETTE_LABELS[p]}
              title={PALETTE_LABELS[p]}
              className={cn(
                "flex h-10 items-center justify-center gap-0.5 rounded-xl border-2 p-1 transition-all",
                "hover:border-primary/40",
                palette === p && "border-primary",
              )}
            >
              {AVATAR_PALETTES[p].map((color, i) => (
                <span
                  key={i}
                  className="size-3 rounded-full"
                  style={{ backgroundColor: color }}
                />
              ))}
            </button>
          ))}
        </div>
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
                "has-[[data-checked]]:border-primary has-[[data-checked]]:bg-primary/10",
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

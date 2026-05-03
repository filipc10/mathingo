"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";

import { UserAvatar } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  AVATAR_PALETTES,
  AVATAR_VARIANTS,
  AvatarPalette,
  AvatarVariant,
} from "@/lib/avatars";
import type { CurrentUser } from "@/lib/auth";
import { cn } from "@/lib/utils";

const PALETTE_LABELS: Record<AvatarPalette, string> = {
  blue: "Modrá",
  green: "Zelená",
  purple: "Fialová",
  sunset: "Západ slunce",
  mono: "Mono",
};

type Props = {
  user: CurrentUser;
  onClose: () => void;
  onSaved: () => void;
};

export function EditProfileModal({ user, onClose, onSaved }: Props) {
  const [displayName, setDisplayName] = useState(user.display_name);
  const [variant, setVariant] = useState<AvatarVariant>(user.avatar_variant);
  const [palette, setPalette] = useState<AvatarPalette>(user.avatar_palette);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  // Close on Escape; lock body scroll while open.
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = previousOverflow;
    };
  }, [onClose]);

  async function handleSave() {
    setSaving(true);
    setError(null);

    const body: Record<string, unknown> = {
      avatar_variant: variant,
      avatar_palette: palette,
    };
    if (displayName !== user.display_name) {
      body.display_name = displayName;
    }

    const res = await fetch("/api/users/me", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      if (res.status === 409) {
        setError("Tato přezdívka je už zabraná. Zkus jinou.");
      } else if (res.status === 422) {
        setError("Přezdívka musí mít 3 až 30 znaků.");
      } else {
        setError("Něco se nepovedlo. Zkus to znovu.");
      }
      setSaving(false);
      return;
    }

    onSaved();
  }

  const previewName = displayName.trim() || "Mathingo";

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="edit-profile-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4 py-6 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative max-h-[calc(100vh-3rem)] w-full max-w-md overflow-y-auto rounded-xl border bg-background p-6 shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <h2
            id="edit-profile-title"
            className="text-lg font-extrabold tracking-tight"
          >
            Upravit profil
          </h2>
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={onClose}
            aria-label="Zavřít"
          >
            <X className="size-4" />
          </Button>
        </div>

        <div className="grid gap-5">
          <div className="flex justify-center">
            <UserAvatar
              name={previewName}
              size={80}
              variant={variant}
              palette={palette}
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="edit-display-name" className="font-bold">
              Přezdívka
            </Label>
            <Input
              id="edit-display-name"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              minLength={3}
              maxLength={30}
              autoComplete="nickname"
            />
            {error && (
              <p role="alert" className="text-sm font-medium text-destructive">
                {error}
              </p>
            )}
          </div>

          <div className="grid gap-2">
            <Label className="font-bold">Styl avataru</Label>
            <div className="grid grid-cols-3 gap-2 sm:grid-cols-6">
              {AVATAR_VARIANTS.map((v) => (
                <button
                  type="button"
                  key={v}
                  onClick={() => setVariant(v)}
                  aria-pressed={variant === v}
                  className={cn(
                    "flex items-center justify-center rounded-lg border-2 p-1.5 transition-all",
                    "hover:border-primary/40 hover:bg-primary/5",
                    variant === v && "border-primary bg-primary/10",
                  )}
                >
                  <UserAvatar
                    name={previewName}
                    size={36}
                    variant={v}
                    palette={palette}
                  />
                </button>
              ))}
            </div>
          </div>

          <div className="grid gap-2">
            <Label className="font-bold">Paleta barev</Label>
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
                    "flex h-9 items-center justify-center gap-0.5 rounded-lg border-2 p-1 transition-all",
                    "hover:border-primary/40",
                    palette === p && "border-primary",
                  )}
                >
                  {AVATAR_PALETTES[p].map((color, i) => (
                    <span
                      key={i}
                      className="size-2.5 rounded-full"
                      style={{ backgroundColor: color }}
                    />
                  ))}
                </button>
              ))}
            </div>
          </div>

          <div className="flex gap-3 pt-2">
            <Button
              variant="outline"
              size="lg"
              onClick={onClose}
              disabled={saving}
              className="flex-1"
            >
              Zrušit
            </Button>
            <Button
              size="lg"
              onClick={handleSave}
              disabled={saving}
              className="flex-1"
            >
              {saving ? "Ukládám…" : "Uložit"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

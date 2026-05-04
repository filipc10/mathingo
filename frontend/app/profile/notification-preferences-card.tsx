"use client";

import { useEffect, useState } from "react";
import { Bell, BellOff } from "lucide-react";
import Link from "next/link";

import { IosInstallGuide } from "@/components/notifications/ios-install-guide";
import {
  SlotPicker,
  type SlotValue,
} from "@/components/notifications/slot-picker";
import { Card, CardContent } from "@/components/ui/card";
import { Toggle } from "@/components/ui/toggle";
import { useDeviceState } from "@/lib/use-device-state";
import { cn } from "@/lib/utils";

type Prefs = {
  enabled: boolean;
  time_slot: SlotValue;
  has_push_subscription: boolean;
};

export function NotificationPreferencesCard() {
  const [prefs, setPrefs] = useState<Prefs | null>(null);
  const [saving, setSaving] = useState(false);
  const deviceState = useDeviceState();

  useEffect(() => {
    void fetchPrefs();
  }, []);

  async function fetchPrefs() {
    const res = await fetch("/api/users/me/notifications", {
      credentials: "same-origin",
    });
    if (res.ok) {
      setPrefs((await res.json()) as Prefs);
    }
  }

  async function updatePrefs(update: Partial<Pick<Prefs, "enabled" | "time_slot">>) {
    if (!prefs) return;

    // Optimistic update — feels instant for the user, the rollback below
    // restores the truth from the server if the network fails.
    const previous = prefs;
    setPrefs({ ...prefs, ...update });
    setSaving(true);

    try {
      const res = await fetch("/api/users/me/notifications", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify(update),
      });
      if (!res.ok) throw new Error("patch_failed");
      const fresh = (await res.json()) as Prefs;
      setPrefs(fresh);
    } catch {
      setPrefs(previous);
    } finally {
      setSaving(false);
    }
  }

  if (!prefs) {
    return (
      <Card>
        <CardContent>
          <div className="h-24 animate-pulse rounded bg-muted" />
        </CardContent>
      </Card>
    );
  }

  // Permission/subscription absent — settings would be a no-op until the
  // user subscribes, so we show a CTA back to /welcome-notifications
  // rather than a fake "enabled" toggle that wouldn't deliver anything.
  if (!prefs.has_push_subscription) {
    // iOS Safari outside PWA mode can't subscribe at all — sending the
    // user to /welcome-notifications would just bounce them off another
    // "iPhone needs install" screen. Show the visual guide here so they
    // know what to do without an extra navigation hop.
    if (deviceState === "ios-needs-install") {
      return (
        <Card>
          <CardContent className="space-y-4">
            <div className="flex items-start gap-3">
              <div className="flex size-10 flex-shrink-0 items-center justify-center rounded-full bg-muted">
                <BellOff className="size-5 text-muted-foreground" />
              </div>
              <div className="flex-1">
                <div className="font-bold">Notifikace na iPhone</div>
                <p className="text-sm text-muted-foreground">
                  Pro denní připomenutí na iPhone potřebujeme Mathingo
                  přidat na plochu. Po instalaci se sem vrať a notifikace
                  povol z plochy.
                </p>
              </div>
            </div>
            <IosInstallGuide />
          </CardContent>
        </Card>
      );
    }

    return (
      <Card>
        <CardContent className="space-y-4">
          <div className="flex items-start gap-3">
            <div className="flex size-10 flex-shrink-0 items-center justify-center rounded-full bg-muted">
              <BellOff className="size-5 text-muted-foreground" />
            </div>
            <div className="flex-1">
              <div className="font-bold">Notifikace nejsou nastavené</div>
              <p className="text-sm text-muted-foreground">
                Pro denní připomenutí potřebujeme povolit notifikace
                a zaregistrovat toto zařízení.
              </p>
            </div>
          </div>
          <Link
            href="/welcome-notifications"
            className="inline-flex h-11 w-full items-center justify-center rounded-xl bg-primary px-4 font-bold text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Povolit notifikace
          </Link>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="space-y-6">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div
              className={cn(
                "flex size-10 flex-shrink-0 items-center justify-center rounded-full",
                prefs.enabled ? "bg-primary/10" : "bg-muted",
              )}
            >
              {prefs.enabled ? (
                <Bell className="size-5 text-primary" />
              ) : (
                <BellOff className="size-5 text-muted-foreground" />
              )}
            </div>
            <div>
              <div className="font-bold">Denní připomenutí</div>
              <p className="text-sm text-muted-foreground">
                {prefs.enabled
                  ? "Posíláme ti připomínku jen ve dnech, kdy ses ještě nestavil."
                  : "Aktuálně ti žádné notifikace neposíláme."}
              </p>
            </div>
          </div>

          <Toggle
            checked={prefs.enabled}
            onChange={(checked) => updatePrefs({ enabled: checked })}
            disabled={saving}
            label="Denní připomenutí"
          />
        </div>

        {prefs.enabled && (
          <div className="space-y-2 border-t border-border pt-4">
            <div className="text-sm font-bold">Kdy?</div>
            <SlotPicker
              value={prefs.time_slot}
              onChange={(slot) => updatePrefs({ time_slot: slot })}
              disabled={saving}
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
}

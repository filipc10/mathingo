"use client";

import { useEffect, useState } from "react";
import { Bell, Loader2, Share2 } from "lucide-react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { vocative } from "@/lib/vocative";

type DeviceState =
  | "checking"
  | "supported" // Android, desktop, iOS in PWA mode
  | "ios-needs-install" // iOS Safari outside PWA — must Add to Home Screen first
  | "unsupported";

export function WelcomeNotificationsClient({
  userFirstName,
}: {
  userFirstName: string;
}) {
  const router = useRouter();
  const [deviceState, setDeviceState] = useState<DeviceState>("checking");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;

    // Check both signals: matchMedia is the modern standard but iOS
    // historically only set navigator.standalone. OR-ing them covers
    // every browser version we support.
    const isStandalone =
      window.matchMedia("(display-mode: standalone)").matches ||
      (window.navigator as Navigator & { standalone?: boolean }).standalone ===
        true;
    const isIOS =
      /iPad|iPhone|iPod/.test(navigator.userAgent) &&
      !(window as unknown as { MSStream?: unknown }).MSStream;
    const supportsPush =
      "serviceWorker" in navigator && "PushManager" in window;

    if (!supportsPush) {
      setDeviceState("unsupported");
    } else if (isIOS && !isStandalone) {
      setDeviceState("ios-needs-install");
    } else {
      setDeviceState("supported");
    }
  }, []);

  async function enableNotifications() {
    setLoading(true);
    setError(null);

    try {
      const permission = await Notification.requestPermission();
      if (permission !== "granted") {
        setError(
          "Notifikace nebyly povoleny. Můžeš je povolit kdykoliv v nastavení.",
        );
        setLoading(false);
        return;
      }

      const vapidRes = await fetch("/api/push/vapid-public-key");
      if (!vapidRes.ok) {
        throw new Error("vapid_unavailable");
      }
      const { key: vapidPublicKey } = await vapidRes.json();

      const reg = await navigator.serviceWorker.ready;
      const subscription = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(vapidPublicKey),
      });

      const subRes = await fetch("/api/push/subscribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify({
          endpoint: subscription.endpoint,
          keys: {
            p256dh: arrayBufferToBase64(subscription.getKey("p256dh")!),
            auth: arrayBufferToBase64(subscription.getKey("auth")!),
          },
          device_label: detectDeviceLabel(),
          user_agent: navigator.userAgent,
        }),
      });

      if (!subRes.ok) {
        throw new Error("subscribe_failed");
      }

      router.push("/learn");
    } catch (e) {
      console.error(e);
      setError("Něco se nepovedlo. Zkus to znovu nebo pokračuj bez notifikací.");
      setLoading(false);
    }
  }

  function skip() {
    router.push("/learn");
  }

  if (deviceState === "checking") {
    return (
      <main className="flex min-h-screen items-center justify-center px-4 py-8">
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
      </main>
    );
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-8">
      <Card className="w-full max-w-lg">
        <CardContent className="space-y-6 py-2">
          <div className="flex justify-center">
            <div className="flex size-16 items-center justify-center rounded-full bg-primary/10">
              <Bell className="size-8 text-primary" />
            </div>
          </div>

          <div className="space-y-2 text-center">
            <h1 className="text-2xl font-extrabold">
              {vocative(userFirstName)}, drobný připomínač?
            </h1>
            <p className="text-muted-foreground">
              Jednou denně ti pošleme krátké upozornění — jen pokud
              ses ještě nestavil. Žádný spam, můžeš změnit nebo
              vypnout kdykoliv.
            </p>
          </div>

          {deviceState === "ios-needs-install" && (
            <div className="space-y-3 rounded-xl bg-muted p-4">
              <div className="font-bold">
                Pro iPhone potřebujeme jeden krok navíc:
              </div>
              <ol className="list-inside list-decimal space-y-2 text-sm">
                <li>
                  Klikni dole na <Share2 className="mx-1 inline size-4" />
                </li>
                <li>
                  Vyber <strong>„Přidat na plochu"</strong>
                </li>
                <li>Otevři Mathingo z plochy a vrať se sem</li>
              </ol>
            </div>
          )}

          {deviceState === "unsupported" && (
            <div className="rounded-xl bg-muted p-4 text-sm">
              Tvůj prohlížeč zatím notifikace nepodporuje. Pokračuj prosím bez
              nich — všechny lekce ti zůstávají k dispozici.
            </div>
          )}

          {error && (
            <div className="rounded-xl border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </div>
          )}

          <div className="space-y-2">
            {deviceState === "supported" && (
              <Button
                onClick={enableNotifications}
                disabled={loading}
                className="w-full"
                size="lg"
              >
                {loading ? (
                  <>
                    <Loader2 className="size-4 animate-spin" />
                    Povoluji…
                  </>
                ) : (
                  "Povolit notifikace"
                )}
              </Button>
            )}

            <Button
              onClick={skip}
              variant="outline"
              className="w-full"
              size="lg"
            >
              Pokračovat bez notifikací
            </Button>
          </div>
        </CardContent>
      </Card>
    </main>
  );
}

// VAPID public key arrives as base64url; pushManager.subscribe wants
// the raw bytes.
function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = atob(base64);
  return Uint8Array.from(rawData, (c) => c.charCodeAt(0));
}

function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

function detectDeviceLabel(): string {
  const ua = navigator.userAgent;
  if (/iPhone/.test(ua)) return "iPhone";
  if (/iPad/.test(ua)) return "iPad";
  if (/Android/.test(ua)) return "Android";
  if (/Macintosh/.test(ua)) return "Mac";
  if (/Windows/.test(ua)) return "Windows";
  return "Unknown";
}

"use client";

import { useEffect, useState } from "react";

export type DeviceState =
  | "checking"
  | "supported" // Android, desktop, iOS in PWA mode
  | "ios-needs-install" // iOS Safari outside PWA — must Add to Home Screen first
  | "unsupported";

/**
 * One-shot capability detection for the push permission flow.
 *
 * Returns "checking" until the first effect runs (server render and
 * the brief moment after hydration), so callers can render a
 * loading state without a separate flag. Both display-mode media
 * query and the legacy navigator.standalone are checked because
 * older iOS only exposed the latter.
 */
export function useDeviceState(): DeviceState {
  const [state, setState] = useState<DeviceState>("checking");

  useEffect(() => {
    if (typeof window === "undefined") return;

    const isStandalone =
      window.matchMedia("(display-mode: standalone)").matches ||
      (window.navigator as Navigator & { standalone?: boolean }).standalone ===
        true;
    const isIOS =
      /iPad|iPhone|iPod/.test(navigator.userAgent) &&
      !(window as unknown as { MSStream?: unknown }).MSStream;
    const supportsPush =
      "serviceWorker" in navigator && "PushManager" in window;

    // iOS check must come BEFORE the push-support check: Safari only
    // exposes window.PushManager once the page is running as an installed
    // PWA, so on iOS Safari outside standalone we'd otherwise mis-classify
    // as "unsupported" and never offer the install guide.
    if (isIOS && !isStandalone) {
      setState("ios-needs-install");
    } else if (!supportsPush) {
      setState("unsupported");
    } else {
      setState("supported");
    }
  }, []);

  return state;
}

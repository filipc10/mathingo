"use client";

import { useEffect } from "react";

// Registers the Service Worker that delivers push notifications. Mounted
// once in the root layout so the worker is available before the user
// reaches /welcome-notifications. Idempotent — repeated calls to register
// are no-ops once the same script URL is already controlling the page.
export function SWRegister() {
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (!("serviceWorker" in navigator)) return;

    navigator.serviceWorker.register("/sw.js").catch((err) => {
      console.error("[SW] registration failed:", err);
    });
  }, []);

  return null;
}

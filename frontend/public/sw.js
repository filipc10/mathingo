// Mathingo Service Worker — push receiver only (no offline caching).
//
// Scope: served at /sw.js → controls the entire origin. We don't intercept
// fetch events on purpose; this worker exists to receive push events and
// route notification clicks. Caching strategies are out of scope for the
// MVP and would warrant a separate design pass.

self.addEventListener("install", () => {
  // Skip waiting so a freshly deployed SW activates on the next page load
  // instead of after every existing tab is closed. Push receivers are
  // backwards-compatible with each other, so the swap is safe.
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("push", (event) => {
  if (!event.data) return;

  let data;
  try {
    data = event.data.json();
  } catch {
    data = { title: "Mathingo", body: event.data.text() };
  }

  const title = data.title || "Mathingo";
  const options = {
    body: data.body || "",
    icon: "/icon-192.png",
    badge: "/icon-192.png",
    // tag dedupes — if a second daily reminder arrives before the first
    // is dismissed, it replaces it instead of stacking. renotify=false so
    // the OS doesn't re-buzz when the same tag is replaced.
    tag: "mathingo-daily-reminder",
    renotify: false,
    requireInteraction: false,
    data: {
      url: data.url || "/learn",
    },
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();

  const targetUrl = (event.notification.data && event.notification.data.url) || "/learn";

  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((clients) => {
      // Prefer focusing an existing Mathingo window over opening a new tab.
      for (const client of clients) {
        if (client.url.startsWith(self.location.origin) && "focus" in client) {
          if ("navigate" in client) {
            client.navigate(targetUrl).catch(() => {});
          }
          return client.focus();
        }
      }
      if (self.clients.openWindow) {
        return self.clients.openWindow(targetUrl);
      }
    }),
  );
});

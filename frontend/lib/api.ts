const isServer = typeof window === "undefined";

const baseUrl = isServer
  ? process.env.BACKEND_INTERNAL_URL ?? "http://backend:8000"
  : process.env.NEXT_PUBLIC_API_URL ?? "/api";

export function apiUrl(path: string): string {
  return `${baseUrl}${path.startsWith("/") ? path : `/${path}`}`;
}

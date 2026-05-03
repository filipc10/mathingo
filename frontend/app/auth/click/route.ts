import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
  const token = req.nextUrl.searchParams.get("token");
  if (!token) {
    return redirect("/signin?error=invalid");
  }

  const backendBase =
    process.env.BACKEND_INTERNAL_URL ?? "http://backend:8000";
  const upstream = await fetch(
    `${backendBase}/auth/click?token=${encodeURIComponent(token)}`,
    { redirect: "manual" },
  );

  const location = upstream.headers.get("location") ?? "/signin?error=invalid";
  return redirect(location);
}

// 302 with a relative Location header. Browsers resolve against the request
// URL, so this stays correct regardless of how Next.js perceives its own
// origin (which behind a reverse proxy can be the internal listen address
// rather than the public host).
function redirect(location: string): NextResponse {
  return new NextResponse(null, {
    status: 302,
    headers: { Location: location },
  });
}

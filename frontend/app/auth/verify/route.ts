import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
  const token = req.nextUrl.searchParams.get("token");
  if (!token) {
    return NextResponse.redirect(
      new URL("/signin?error=invalid_or_expired", req.url),
    );
  }

  const backendBase =
    process.env.BACKEND_INTERNAL_URL ?? "http://backend:8000";
  const upstream = await fetch(
    `${backendBase}/auth/verify?token=${encodeURIComponent(token)}`,
    { redirect: "manual" },
  );

  const location =
    upstream.headers.get("location") ?? "/signin?error=invalid_or_expired";
  const setCookie = upstream.headers.get("set-cookie");

  const response = NextResponse.redirect(new URL(location, req.url));
  if (setCookie) {
    response.headers.set("set-cookie", setCookie);
  }
  return response;
}

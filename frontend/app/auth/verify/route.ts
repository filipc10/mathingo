import { NextRequest, NextResponse } from "next/server";

// Legacy redirect. Magic-link emails sent before the two-step split pointed
// here; forward them to /auth/click so in-flight emails still work for the
// 15-minute TTL window after the deploy.
export async function GET(req: NextRequest) {
  const token = req.nextUrl.searchParams.get("token");
  const target = token
    ? `/auth/click?token=${encodeURIComponent(token)}`
    : "/signin?error=invalid";

  return new NextResponse(null, {
    status: 302,
    headers: { Location: target },
  });
}

import { redirect } from "next/navigation";

import { ClickClient } from "./click-client";

type Props = {
  searchParams: Promise<{ token?: string }>;
};

export default async function ClickPage({ searchParams }: Props) {
  const params = await searchParams;
  if (!params.token) redirect("/signin?error=invalid");

  return <ClickClient token={params.token} />;
}

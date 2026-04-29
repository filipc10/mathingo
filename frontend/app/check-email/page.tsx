import Link from "next/link";
import { Mail } from "lucide-react";

import { buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";

export default function CheckEmailPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-6 py-12">
      <Card className="w-full max-w-md text-center">
        <CardHeader className="items-center gap-4">
          <div className="flex size-16 items-center justify-center rounded-full bg-primary/10 text-primary">
            <Mail className="size-8" />
          </div>
          <CardTitle className="text-2xl font-extrabold tracking-tight">
            Mrkni do schránky
          </CardTitle>
          <CardDescription className="text-base">
            Poslali jsme ti přihlašovací odkaz.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-5">
          <p className="text-sm font-medium text-muted-foreground">
            Klikni na tlačítko v e-mailu pro přihlášení do aplikace. Odkaz je
            platný 15 minut.
          </p>
          <Link
            href="/signin"
            className={cn(buttonVariants({ variant: "outline" }), "w-full")}
          >
            Zpět na přihlášení
          </Link>
        </CardContent>
      </Card>
    </main>
  );
}

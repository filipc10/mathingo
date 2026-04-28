import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function CheckEmailPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-white px-6 dark:bg-neutral-950">
      <Card className="w-full max-w-sm text-center">
        <CardHeader>
          <CardTitle>Mrkni do schránky</CardTitle>
          <CardDescription>
            Poslali jsme ti přihlašovací odkaz.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Klikni na tlačítko v emailu pro přihlášení do aplikace. Odkaz je
            platný 15 minut.
          </p>
        </CardContent>
      </Card>
    </main>
  );
}

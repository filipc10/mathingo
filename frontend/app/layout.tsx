import type { Metadata } from "next";
import { Nunito } from "next/font/google";
import { Toaster } from "@/components/ui/sonner";
import "katex/dist/katex.min.css";
import "./globals.css";

const nunito = Nunito({
  subsets: ["latin", "latin-ext"],
  weight: ["400", "600", "700", "800", "900"],
  variable: "--font-nunito",
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_APP_URL ?? "https://mathingo.cz",
  ),
  title: "Mathingo",
  description: "Procvičování matematiky ve stylu Duolinga.",
  manifest: "/manifest.json",
  // iOS Safari ignores the web manifest's `display: standalone` — it needs
  // these legacy Apple meta tags to render Add-to-Home-Screen as a real
  // PWA shell, which is the only mode where iOS allows Web Push at all.
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "Mathingo",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="cs" className={`dark ${nunito.variable}`}>
      <body className="antialiased">
        {children}
        <Toaster />
      </body>
    </html>
  );
}

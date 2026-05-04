import type { ReactNode } from "react";

/**
 * 3-step visual guide for installing Mathingo as an iOS PWA.
 *
 * SVG illustrations are inline so they ship with the JS bundle —
 * no extra image fetch, no asset pipeline, and they auto-adapt to
 * dark / light mode through `currentColor` + Tailwind text-color
 * utilities. The accent paths are wrapped in `<g className="text-primary">`
 * which sets a local CSS `color`; descendants resolve `currentColor`
 * to that value. Neutral paths inherit the parent text color (muted)
 * via `text-muted-foreground` on the wrapping container.
 */
export function IosInstallGuide() {
  return (
    <div className="space-y-3 rounded-xl bg-muted/40 p-4 text-muted-foreground">
      <div className="text-center text-sm font-bold text-foreground">
        Pro iPhone potřebuješ Mathingo přidat na plochu:
      </div>

      <div className="space-y-2">
        <Step number={1} description="Klikni na ikonu sdílení dole v Safari">
          <ShareIconIllustration />
        </Step>
        <Step number={2} description="V menu vyber „Přidat na plochu“">
          <AddToHomeScreenIllustration />
        </Step>
        <Step
          number={3}
          description="Otevři Mathingo z plochy a klikni na svůj profil, kde povolíš notifikace"
        >
          <HomeScreenIllustration />
        </Step>
      </div>
    </div>
  );
}

function Step({
  number,
  description,
  children,
}: {
  number: number;
  description: string;
  children: ReactNode;
}) {
  return (
    <div className="flex items-center gap-3 rounded-lg bg-card/60 p-3">
      <div
        aria-hidden
        className="flex size-7 flex-shrink-0 items-center justify-center rounded-full bg-primary text-sm font-bold text-primary-foreground"
      >
        {number}
      </div>
      <div className="flex size-16 flex-shrink-0 items-center justify-center">
        {children}
      </div>
      <div className="flex-1 text-sm text-foreground">{description}</div>
    </div>
  );
}

function ShareIconIllustration() {
  return (
    <svg
      viewBox="0 0 64 64"
      className="size-12"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      {/* Subtle Safari toolbar context */}
      <rect
        x="4"
        y="48"
        width="56"
        height="12"
        rx="3"
        fill="currentColor"
        opacity="0.15"
      />

      <g className="text-primary">
        {/* Open box (the share container) */}
        <path
          d="M20 28 L20 50 L44 50 L44 28"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
        />
        {/* Up arrow inside */}
        <path
          d="M32 16 L32 38 M24 24 L32 16 L40 24"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </g>
    </svg>
  );
}

function AddToHomeScreenIllustration() {
  return (
    <svg
      viewBox="0 0 64 64"
      className="size-12"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      {/* Menu sheet background */}
      <rect
        x="4"
        y="8"
        width="56"
        height="48"
        rx="6"
        fill="currentColor"
        opacity="0.1"
      />

      {/* Top dimmed item */}
      <line
        x1="14"
        y1="18"
        x2="42"
        y2="18"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        opacity="0.4"
      />

      <g className="text-primary">
        {/* Highlighted "Add to Home Screen" row */}
        <rect
          x="6"
          y="26"
          width="52"
          height="14"
          rx="3"
          fill="currentColor"
          opacity="0.2"
        />
        {/* Plus-in-square icon */}
        <rect
          x="11"
          y="29"
          width="8"
          height="8"
          rx="1.5"
          stroke="currentColor"
          strokeWidth="1.5"
          fill="none"
        />
        <line
          x1="15"
          y1="31"
          x2="15"
          y2="35"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
        />
        <line
          x1="13"
          y1="33"
          x2="17"
          y2="33"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
        />
        {/* Label line for the highlighted row */}
        <line
          x1="22"
          y1="33"
          x2="50"
          y2="33"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
        />
      </g>

      {/* Bottom dimmed item */}
      <line
        x1="14"
        y1="48"
        x2="42"
        y2="48"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        opacity="0.4"
      />
    </svg>
  );
}

function HomeScreenIllustration() {
  return (
    <svg
      viewBox="0 0 64 64"
      className="size-12"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      {/* Phone frame */}
      <rect
        x="14"
        y="6"
        width="36"
        height="52"
        rx="5"
        stroke="currentColor"
        strokeWidth="2"
        opacity="0.5"
      />
      {/* Notch */}
      <rect
        x="26"
        y="6"
        width="12"
        height="3"
        rx="1.5"
        fill="currentColor"
        opacity="0.5"
      />

      {/* Surrounding apps — dim circles */}
      <circle cx="22" cy="20" r="2.5" fill="currentColor" opacity="0.35" />
      <circle cx="32" cy="20" r="2.5" fill="currentColor" opacity="0.35" />
      <circle cx="42" cy="20" r="2.5" fill="currentColor" opacity="0.35" />
      <circle cx="22" cy="32" r="2.5" fill="currentColor" opacity="0.35" />
      <circle cx="42" cy="32" r="2.5" fill="currentColor" opacity="0.35" />
      <circle cx="22" cy="44" r="2.5" fill="currentColor" opacity="0.35" />
      <circle cx="32" cy="44" r="2.5" fill="currentColor" opacity="0.35" />
      <circle cx="42" cy="44" r="2.5" fill="currentColor" opacity="0.35" />

      {/* Mathingo app — accent square with M */}
      <g className="text-primary">
        <rect x="28" y="28" width="8" height="8" rx="1.5" fill="currentColor" />
      </g>
      <text
        x="32"
        y="34.5"
        textAnchor="middle"
        fontSize="6"
        fontWeight="bold"
        fill="white"
      >
        M
      </text>
    </svg>
  );
}

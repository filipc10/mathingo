export const AVATAR_VARIANTS = [
  "marble",
  "beam",
  "pixel",
  "sunset",
  "ring",
  "bauhaus",
] as const;

export type AvatarVariant = (typeof AVATAR_VARIANTS)[number];

export const AVATAR_PALETTES = {
  blue: ["#0073FF", "#3B82F6", "#06B6D4", "#22D3EE", "#0EA5E9"],
  green: ["#16A34A", "#22C55E", "#4ADE80", "#84CC16", "#10B981"],
  purple: ["#7C3AED", "#8B5CF6", "#A855F7", "#D946EF", "#EC4899"],
  sunset: ["#F97316", "#FB923C", "#F59E0B", "#EF4444", "#FACC15"],
  mono: ["#0F172A", "#334155", "#64748B", "#94A3B8", "#CBD5E1"],
} as const satisfies Record<string, readonly string[]>;

export type AvatarPalette = keyof typeof AVATAR_PALETTES;

export const DEFAULT_AVATAR_VARIANT: AvatarVariant = "beam";
export const DEFAULT_AVATAR_PALETTE: AvatarPalette = "blue";

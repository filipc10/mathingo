"use client";

import Avatar from "boring-avatars";

import {
  AVATAR_PALETTES,
  AvatarPalette,
  AvatarVariant,
  DEFAULT_AVATAR_PALETTE,
  DEFAULT_AVATAR_VARIANT,
} from "@/lib/avatars";

export function UserAvatar({
  name,
  size = 40,
  variant = DEFAULT_AVATAR_VARIANT,
  palette = DEFAULT_AVATAR_PALETTE,
}: {
  name: string;
  size?: number;
  variant?: AvatarVariant;
  palette?: AvatarPalette;
}) {
  return (
    <Avatar
      name={name}
      variant={variant}
      size={size}
      colors={[...AVATAR_PALETTES[palette]]}
    />
  );
}

"use client";

import Avatar from "boring-avatars";

const PALETTE = ["#0073FF", "#22C55E", "#3B82F6", "#06B6D4", "#8B5CF6"];

export function UserAvatar({
  name,
  size = 40,
}: {
  name: string;
  size?: number;
}) {
  return (
    <Avatar name={name} variant="beam" size={size} colors={PALETTE} />
  );
}

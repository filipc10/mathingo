"use client";

import { Moon, Sun, Sunrise } from "lucide-react";

import { cn } from "@/lib/utils";

const SLOTS = [
  { value: "morning", label: "Ráno", time: "8:00", Icon: Sunrise },
  { value: "noon", label: "Poledne", time: "12:00", Icon: Sun },
  { value: "evening", label: "Večer", time: "18:00", Icon: Moon },
] as const;

export type SlotValue = (typeof SLOTS)[number]["value"];

export function SlotPicker({
  value,
  onChange,
  disabled = false,
}: {
  value: SlotValue;
  onChange: (slot: SlotValue) => void;
  disabled?: boolean;
}) {
  return (
    <div
      role="radiogroup"
      aria-label="Čas notifikace"
      className="grid grid-cols-3 gap-2 rounded-xl bg-muted p-1"
    >
      {SLOTS.map((slot) => {
        const isActive = value === slot.value;
        return (
          <button
            key={slot.value}
            type="button"
            role="radio"
            aria-checked={isActive}
            onClick={() => !disabled && onChange(slot.value)}
            disabled={disabled}
            className={cn(
              "flex flex-col items-center gap-1 rounded-lg px-2 py-3 transition-all",
              isActive
                ? "border border-primary/20 bg-card shadow-sm"
                : "hover:bg-card/50",
              disabled && "cursor-not-allowed opacity-60",
            )}
          >
            <slot.Icon
              className={cn(
                "size-5",
                isActive ? "text-primary" : "text-muted-foreground",
              )}
            />
            <div
              className={cn(
                "text-sm font-bold",
                isActive ? "text-foreground" : "text-muted-foreground",
              )}
            >
              {slot.label}
            </div>
            <div className="text-xs tabular-nums text-muted-foreground">
              {slot.time}
            </div>
          </button>
        );
      })}
    </div>
  );
}

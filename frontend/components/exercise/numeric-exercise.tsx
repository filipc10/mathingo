"use client";

import { Input } from "@/components/ui/input";

import { KaTeXRenderer } from "./katex-renderer";

export function NumericExercise({
  prompt,
  value,
  onChange,
}: {
  prompt: string;
  value: number | null;
  onChange: (value: number | null) => void;
}) {
  return (
    <div className="space-y-6">
      <div className="text-xl font-bold leading-relaxed">
        <KaTeXRenderer text={prompt} />
      </div>
      <Input
        type="number"
        step="any"
        inputMode="decimal"
        value={value ?? ""}
        onChange={(e) => {
          const raw = e.target.value;
          if (raw === "") {
            onChange(null);
          } else {
            const parsed = parseFloat(raw);
            onChange(Number.isNaN(parsed) ? null : parsed);
          }
        }}
        placeholder="Tvoje odpověď"
        className="h-16 text-center text-2xl font-bold"
      />
    </div>
  );
}

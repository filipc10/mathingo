"use client";

import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

import { KaTeXRenderer } from "./katex-renderer";

type Phase = "answering" | "feedback";

export function NumericExercise({
  prompt,
  value,
  onChange,
  phase = "answering",
}: {
  prompt: string;
  value: number | null;
  onChange: (value: number | null) => void;
  phase?: Phase;
}) {
  const frozen = phase === "feedback";

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
        disabled={frozen}
        readOnly={frozen}
        className={cn(
          "h-16 text-center text-2xl font-bold",
          frozen && "cursor-not-allowed opacity-80",
        )}
      />
    </div>
  );
}

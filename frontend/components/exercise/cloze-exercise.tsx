"use client";

import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

import { KaTeXRenderer } from "./katex-renderer";

export type ClozePayload = {
  placeholder?: string | null;
};

type Phase = "answering" | "feedback";

export function ClozeExercise({
  prompt,
  payload,
  value,
  onChange,
  phase = "answering",
}: {
  prompt: string;
  payload: ClozePayload;
  value: string;
  onChange: (value: string) => void;
  phase?: Phase;
}) {
  const frozen = phase === "feedback";

  return (
    <div className="space-y-6">
      <div className="text-xl font-bold leading-relaxed">
        <KaTeXRenderer text={prompt} />
      </div>
      <Input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={payload.placeholder ?? "tvoje odpověď"}
        disabled={frozen}
        readOnly={frozen}
        autoComplete="off"
        autoCapitalize="none"
        spellCheck={false}
        className={cn(
          "h-16 text-center text-xl font-bold",
          frozen && "cursor-not-allowed opacity-80",
        )}
      />
    </div>
  );
}

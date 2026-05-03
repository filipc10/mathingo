import { Card, CardContent } from "@/components/ui/card";
import type { TypeStats } from "@/lib/api";

const TYPE_LABELS: Record<string, string> = {
  multiple_choice: "Výběr odpovědi",
  numeric: "Numerická odpověď",
  true_false: "Pravda / nepravda",
  matching: "Spojování",
  step_ordering: "Řazení kroků",
};

export function TypeStatsBlock({ data }: { data: TypeStats[] }) {
  if (data.length === 0) {
    return (
      <Card>
        <CardContent className="text-center text-muted-foreground">
          Zatím žádná data — vyřeš nějaké cvičení.
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-3 md:grid-cols-2 md:gap-4">
      {data.map((typ) => {
        const winrate = typ.total_attempts
          ? typ.correct_attempts / typ.total_attempts
          : 0;
        const label = TYPE_LABELS[typ.exercise_type] ?? typ.exercise_type;
        return (
          <Card key={typ.exercise_type}>
            <CardContent className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold">{label}</span>
                <span className="text-2xl font-extrabold">
                  {(winrate * 100).toFixed(0)}%
                </span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full bg-primary"
                  style={{ width: `${winrate * 100}%` }}
                />
              </div>
              <p className="text-sm text-muted-foreground">
                {typ.correct_attempts} z {typ.total_attempts} správně
              </p>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

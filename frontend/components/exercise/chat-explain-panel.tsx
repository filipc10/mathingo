"use client";

import { useEffect, useRef, useState } from "react";
import { Loader2, Send, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { apiUrl } from "@/lib/api";
import type { AnswerValue } from "@/app/lesson/[id]/actions";

import { KaTeXRenderer } from "./katex-renderer";

type ChatRole = "user" | "assistant";

type ChatMessage = {
  role: ChatRole;
  content: string;
};

const SESSION_LIMIT = 5;

export function ChatExplainPanel({
  exerciseId,
  userAnswer,
}: {
  exerciseId: string;
  userAnswer: AnswerValue;
}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [usage, setUsage] = useState<{ used: number; limit: number } | null>(
    null,
  );
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const userTurnsSent = messages.filter((m) => m.role === "user").length;
  const sessionLimitReached = userTurnsSent >= SESSION_LIMIT;
  const dailyLimitReached =
    usage !== null && usage.used >= usage.limit && !streaming;

  // Default first prompt: a one-click "vysvětli mi to" that sends an
  // empty-but-meaningful question. This way the student never stares at
  // an empty chat box wondering what to type.
  const isFirstTurn = messages.length === 0;

  async function sendMessage(text: string) {
    if (!text.trim() || streaming) return;
    setError(null);

    const nextHistory: ChatMessage[] = [
      ...messages,
      { role: "user", content: text },
    ];
    setMessages(nextHistory);
    setDraft("");

    // Append an empty assistant message we'll fill in chunk by chunk.
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);
    setStreaming(true);

    try {
      const res = await fetch(apiUrl(`/exercises/${exerciseId}/explain`), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          user_answer: userAnswer,
          messages: nextHistory,
        }),
      });

      if (!res.ok) {
        const detail = await res.text();
        if (res.status === 429) {
          setError(
            detail.includes("session")
              ? "Limit zpráv pro tuto lekci jsi vyčerpal/a."
              : "Denní limit AI dotazů jsi vyčerpal/a. Zkus to zítra.",
          );
        } else if (res.status === 503) {
          setError("AI chat zatím není nakonfigurovaný.");
        } else {
          setError("Něco se pokazilo. Zkus to znovu za chvíli.");
        }
        // Roll back the optimistic assistant placeholder + the user turn.
        setMessages(messages);
        setStreaming(false);
        return;
      }

      if (!res.body) {
        setError("Spojení se serverem selhalo.");
        setMessages(messages);
        setStreaming(false);
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let assistantText = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        // SSE frames are separated by a blank line.
        const frames = buffer.split("\n\n");
        buffer = frames.pop() ?? "";

        for (const frame of frames) {
          let event = "message";
          let data = "";
          for (const line of frame.split("\n")) {
            if (line.startsWith("event:")) event = line.slice(6).trim();
            else if (line.startsWith("data:")) data += line.slice(5).trim();
          }
          if (!data) continue;

          if (event === "usage") {
            try {
              const meta = JSON.parse(data) as {
                messages_used_today: number;
                daily_limit: number;
              };
              setUsage({ used: meta.messages_used_today, limit: meta.daily_limit });
            } catch {
              /* ignore */
            }
          } else if (event === "token") {
            try {
              const { text: chunk } = JSON.parse(data) as { text: string };
              assistantText += chunk;
              setMessages((prev) => {
                const out = prev.slice(0, -1);
                out.push({ role: "assistant", content: assistantText });
                return out;
              });
            } catch {
              /* ignore */
            }
          } else if (event === "error") {
            setError("AI vrátila chybu. Zkus to znovu za chvíli.");
          }
        }
      }
    } catch {
      setError("Spojení se serverem selhalo.");
      setMessages(messages);
    } finally {
      setStreaming(false);
    }
  }

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="space-y-3 rounded-xl border bg-card p-4">
      <div className="flex items-center gap-2 text-sm font-bold text-primary">
        <Sparkles className="size-4" />
        AI vysvětlení
        {usage && (
          <span className="ml-auto text-xs font-medium text-muted-foreground">
            {usage.used} / {usage.limit} dnes
          </span>
        )}
      </div>

      <div
        ref={scrollRef}
        className="max-h-72 space-y-3 overflow-y-auto pr-1 text-sm"
      >
        {messages.map((m, i) => (
          <div
            key={i}
            className={
              m.role === "user"
                ? "ml-6 rounded-lg bg-primary/10 px-3 py-2 font-medium"
                : "mr-6 rounded-lg bg-muted px-3 py-2 leading-relaxed"
            }
          >
            {m.content === "" && streaming ? (
              <Loader2 className="size-4 animate-spin text-muted-foreground" />
            ) : (
              <KaTeXRenderer text={m.content} />
            )}
          </div>
        ))}
        {messages.length === 0 && (
          <p className="text-muted-foreground">
            Zeptej se na cokoli, co ti není jasné. AI ti to vysvětlí krok za krokem.
          </p>
        )}
      </div>

      {error && (
        <p className="text-xs font-medium text-destructive">{error}</p>
      )}

      {isFirstTurn ? (
        <Button
          size="lg"
          className="w-full"
          disabled={streaming || dailyLimitReached}
          onClick={() => sendMessage("Vysvětli mi prosím, proč jsem to měl/a špatně.")}
        >
          {streaming ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            "Vysvětli mi to krok za krokem"
          )}
        </Button>
      ) : (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            sendMessage(draft);
          }}
          className="flex gap-2"
        >
          <Input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder={
              sessionLimitReached
                ? "Limit zpráv pro tuto lekci je vyčerpaný."
                : "Zeptej se…"
            }
            disabled={streaming || sessionLimitReached || dailyLimitReached}
          />
          <Button
            type="submit"
            size="icon"
            disabled={
              streaming ||
              !draft.trim() ||
              sessionLimitReached ||
              dailyLimitReached
            }
            aria-label="Odeslat zprávu"
          >
            {streaming ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Send className="size-4" />
            )}
          </Button>
        </form>
      )}

      {!error && sessionLimitReached && !streaming && (
        <p className="text-xs font-medium text-muted-foreground">
          Vyčerpal/a jsi limit {SESSION_LIMIT} zpráv pro toto cvičení.
        </p>
      )}
    </div>
  );
}

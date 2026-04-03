"use client";

import { useState } from "react";
import { Bookmark, EyeOff, Star, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { papers as papersApi } from "@/lib/api";
import { cn } from "@/lib/utils";

interface InteractionButtonsProps {
  paperId: string;
  currentAction: string | null;
  onActionChange?: (action: string | null) => void;
}

export function InteractionButtons({
  paperId,
  currentAction,
  onActionChange,
}: InteractionButtonsProps) {
  const [action, setAction] = useState<string | null>(currentAction);
  const [loading, setLoading] = useState<string | null>(null);

  const handleInteract = async (newAction: string) => {
    const effectiveAction = action === newAction ? "none" : newAction;
    setLoading(newAction);
    try {
      await papersApi.interact(paperId, effectiveAction);
      const updated = effectiveAction === "none" ? null : effectiveAction;
      setAction(updated);
      onActionChange?.(updated);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Action failed");
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="flex items-center gap-1">
      <button
        onClick={() => handleInteract("saved")}
        disabled={loading !== null}
        title="Save paper"
        className={cn(
          "p-1.5 rounded-md transition-colors",
          action === "saved"
            ? "text-indigo-600 bg-indigo-50"
            : "text-zinc-400 hover:text-zinc-600 hover:bg-zinc-100"
        )}
      >
        {loading === "saved" ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Bookmark className={cn("h-4 w-4", action === "saved" && "fill-current")} />
        )}
      </button>
      <button
        onClick={() => handleInteract("ignored")}
        disabled={loading !== null}
        title="Ignore paper"
        className={cn(
          "p-1.5 rounded-md transition-colors",
          action === "ignored"
            ? "text-red-500 bg-red-50"
            : "text-zinc-400 hover:text-zinc-600 hover:bg-zinc-100"
        )}
      >
        {loading === "ignored" ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <EyeOff className={cn("h-4 w-4", action === "ignored" && "fill-current")} />
        )}
      </button>
      <button
        onClick={() => handleInteract("highly_relevant")}
        disabled={loading !== null}
        title="Mark as highly relevant"
        className={cn(
          "p-1.5 rounded-md transition-colors",
          action === "highly_relevant"
            ? "text-amber-500 bg-amber-50"
            : "text-zinc-400 hover:text-zinc-600 hover:bg-zinc-100"
        )}
      >
        {loading === "highly_relevant" ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Star className={cn("h-4 w-4", action === "highly_relevant" && "fill-current")} />
        )}
      </button>
    </div>
  );
}

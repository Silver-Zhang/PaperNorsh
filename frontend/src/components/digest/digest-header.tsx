"use client";

import { format } from "date-fns";
import { Badge } from "@/components/ui/badge";
import type { DailyDigest } from "@/types";

interface DigestHeaderProps {
  digest: DailyDigest | null;
}

export function DigestHeader({ digest }: DigestHeaderProps) {
  const paperCount = digest?.papers?.length ?? 0;
  const status = digest?.status ?? "pending";

  return (
    <div className="mb-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-zinc-900">Today&apos;s Digest</h2>
          <p className="text-zinc-500 text-sm mt-1">
            {format(new Date(), "EEEE, MMMM d, yyyy")}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-zinc-500">
            {paperCount} paper{paperCount !== 1 ? "s" : ""} curated for you
          </span>
          <Badge variant={status === "completed" ? "default" : "secondary"}>
            {status}
          </Badge>
        </div>
      </div>
    </div>
  );
}

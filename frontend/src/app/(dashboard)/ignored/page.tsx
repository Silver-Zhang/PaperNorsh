"use client";

import useSWR from "swr";
import { papers as papersApi } from "@/lib/api";
import { PaperList } from "@/components/papers/paper-list";
import { Card, CardContent } from "@/components/ui/card";
import type { PaperWithScore } from "@/types";

export default function IgnoredPage() {
  const { data, error, isLoading } = useSWR<PaperWithScore[]>(
    "ignored-papers",
    () => papersApi.getIgnored() as Promise<PaperWithScore[]>
  );

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-zinc-900">Ignored Papers</h2>
        <p className="text-zinc-500 text-sm mt-1">
          {data ? `${data.length} paper${data.length !== 1 ? "s" : ""} ignored` : ""}
        </p>
      </div>

      {isLoading && (
        <Card>
          <CardContent className="p-6">
            <div className="animate-pulse space-y-3">
              <div className="h-4 bg-zinc-200 rounded w-3/4" />
              <div className="h-3 bg-zinc-200 rounded w-1/2" />
            </div>
          </CardContent>
        </Card>
      )}

      {error && (
        <p className="text-red-500 text-sm">Failed to load ignored papers.</p>
      )}

      {!isLoading && !error && (
        <PaperList papers={data ?? []} />
      )}
    </div>
  );
}

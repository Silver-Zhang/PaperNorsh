"use client";

import { useState, useEffect } from "react";
import useSWR from "swr";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import { digest as digestApi, papers as papersApi } from "@/lib/api";
import { DigestHeader } from "@/components/digest/digest-header";
import { PaperList } from "@/components/papers/paper-list";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { DailyDigest, Paper, PaperWithScore } from "@/types";

function SkeletonCard() {
  return (
    <Card className="mb-4">
      <CardContent className="p-6">
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-zinc-200 rounded w-3/4" />
          <div className="h-3 bg-zinc-200 rounded w-1/2" />
          <div className="h-3 bg-zinc-200 rounded w-full" />
          <div className="h-3 bg-zinc-200 rounded w-5/6" />
        </div>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const { data: digestData, error: digestError, isLoading: digestLoading } = useSWR<DailyDigest>(
    "today-digest",
    () => digestApi.getTodayDigest() as Promise<DailyDigest>
  );

  const [papers, setPapers] = useState<PaperWithScore[]>([]);
  const [papersLoading, setPapersLoading] = useState(false);
  const [isTriggering, setIsTriggering] = useState(false);

  useEffect(() => {
    if (!digestData?.papers?.length) return;
    setPapersLoading(true);
    Promise.all(
      digestData.papers.map((item) =>
        (papersApi.getPaper(item.paper_id) as Promise<Paper>).then((p) => ({
          ...p,
          relevance_score: item.relevance_score,
          score_breakdown: {},
          user_action: null,
        } as PaperWithScore))
      )
    )
      .then(setPapers)
      .catch(() => toast.error("Failed to load paper details"))
      .finally(() => setPapersLoading(false));
  }, [digestData]);

  const handleTrigger = async () => {
    setIsTriggering(true);
    try {
      await digestApi.triggerDigest();
      toast.success("Digest triggered! Refresh in a moment.");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to trigger digest");
    } finally {
      setIsTriggering(false);
    }
  };

  const isLoading = digestLoading || papersLoading;

  return (
    <div>
      <DigestHeader digest={digestData ?? null} />

      {digestError && (
        <Card className="mb-4">
          <CardContent className="p-6 text-center">
            <p className="text-zinc-500 mb-4">Could not load today&apos;s digest.</p>
            <Button onClick={handleTrigger} disabled={isTriggering}>
              {isTriggering && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Generate Today&apos;s Digest
            </Button>
          </CardContent>
        </Card>
      )}

      {!digestError && isLoading && (
        <>
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </>
      )}

      {!digestError && !isLoading && (!digestData || digestData.papers?.length === 0) && (
        <Card>
          <CardContent className="p-6 text-center">
            <p className="text-lg font-medium text-zinc-900 mb-1">No digest yet</p>
            <p className="text-zinc-500 text-sm mb-4">
              Generate your first digest to see curated papers.
            </p>
            <Button onClick={handleTrigger} disabled={isTriggering}>
              {isTriggering && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Generate Today&apos;s Digest
            </Button>
          </CardContent>
        </Card>
      )}

      {!digestError && !isLoading && papers.length > 0 && (
        <PaperList papers={papers} />
      )}
    </div>
  );
}

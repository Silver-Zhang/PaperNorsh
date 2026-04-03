"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import useSWR from "swr";
import { format, parseISO } from "date-fns";
import {
  ArrowLeft,
  ExternalLink,
  Sparkles,
} from "lucide-react";
import { papers as papersApi } from "@/lib/api";
import { InteractionButtons } from "@/components/papers/interaction-buttons";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import type { PaperWithScore } from "@/types";

function sourceVariant(source: string) {
  switch (source.toLowerCase()) {
    case "arxiv":
      return "bg-indigo-100 text-indigo-800";
    case "openalex":
      return "bg-green-100 text-green-800";
    case "crossref":
      return "bg-orange-100 text-orange-800";
    default:
      return "bg-zinc-100 text-zinc-800";
  }
}

export default function PaperDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const { data: paper, error, isLoading } = useSWR<PaperWithScore>(
    id ? `paper-${id}` : null,
    () => papersApi.getPaper(id) as Promise<PaperWithScore>
  );

  const [userAction, setUserAction] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className="max-w-3xl mx-auto py-8 px-4">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-zinc-200 rounded w-3/4" />
          <div className="h-4 bg-zinc-200 rounded w-1/2" />
          <div className="h-32 bg-zinc-200 rounded" />
        </div>
      </div>
    );
  }

  if (error || !paper) {
    return (
      <div className="max-w-3xl mx-auto py-8 px-4 text-center">
        <p className="text-zinc-500">Paper not found.</p>
        <Button variant="ghost" onClick={() => router.back()} className="mt-4">
          <ArrowLeft className="mr-2 h-4 w-4" /> Go Back
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto py-4">
      <Button variant="ghost" size="sm" onClick={() => router.back()} className="mb-6">
        <ArrowLeft className="mr-2 h-4 w-4" /> Back
      </Button>

      <div className="flex items-start justify-between gap-4 mb-4">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold", sourceVariant(paper.source))}>
            {paper.source}
          </span>
          {paper.relevance_score > 0 && (
            <Badge variant="outline">Score: {Math.round(paper.relevance_score * 100) / 100}</Badge>
          )}
          {paper.published_date && (
            <span className="text-xs text-zinc-400">
              {format(parseISO(paper.published_date), "MMMM d, yyyy")}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <InteractionButtons
            paperId={paper.id}
            currentAction={paper.user_action ?? userAction}
            onActionChange={setUserAction}
          />
          <a
            href={paper.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-sm text-indigo-600 hover:underline"
          >
            <ExternalLink className="h-4 w-4" /> Open
          </a>
        </div>
      </div>

      <h1 className="text-2xl font-bold text-zinc-900 mb-4 leading-tight">
        {paper.title}
      </h1>

      {paper.authors.length > 0 && (
        <div className="mb-4">
          <h3 className="text-sm font-semibold text-zinc-700 mb-2">Authors</h3>
          <div className="flex flex-wrap gap-2">
            {paper.authors.map((author, i) => (
              <div key={i} className="text-sm">
                <span className="text-zinc-900">{author.name}</span>
                {author.affiliation && (
                  <span className="text-zinc-500 text-xs ml-1">({author.affiliation})</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      <Separator className="my-4" />

      {(paper.doi || paper.arxiv_id || paper.journal_name) && (
        <div className="mb-4 flex flex-wrap gap-4 text-sm">
          {paper.doi && (
            <div>
              <span className="text-zinc-500 text-xs uppercase tracking-wide">DOI</span>
              <a
                href={`https://doi.org/${paper.doi}`}
                target="_blank"
                rel="noopener noreferrer"
                className="block text-indigo-600 hover:underline"
              >
                {paper.doi}
              </a>
            </div>
          )}
          {paper.arxiv_id && (
            <div>
              <span className="text-zinc-500 text-xs uppercase tracking-wide">arXiv</span>
              <a
                href={`https://arxiv.org/abs/${paper.arxiv_id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="block text-indigo-600 hover:underline"
              >
                {paper.arxiv_id}
              </a>
            </div>
          )}
          {paper.journal_name && (
            <div>
              <span className="text-zinc-500 text-xs uppercase tracking-wide">Journal</span>
              <p className="text-zinc-900">{paper.journal_name}</p>
            </div>
          )}
        </div>
      )}

      {paper.abstract && (
        <Card className="mb-4">
          <CardHeader>
            <CardTitle className="text-base">Abstract</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-zinc-700 leading-relaxed">{paper.abstract}</p>
          </CardContent>
        </Card>
      )}

      {paper.ai_summary && (
        <Card className="mb-4 border-indigo-200 bg-indigo-50">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-indigo-600" />
              AI Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-indigo-900 leading-relaxed">{paper.ai_summary}</p>
          </CardContent>
        </Card>
      )}

      {paper.keywords.length > 0 && (
        <div className="mb-4">
          <h3 className="text-sm font-semibold text-zinc-700 mb-2">Keywords</h3>
          <div className="flex flex-wrap gap-2">
            {paper.keywords.map((kw, i) => (
              <Badge key={i} variant="secondary">{kw}</Badge>
            ))}
          </div>
        </div>
      )}

      {paper.score_breakdown && Object.keys(paper.score_breakdown).length > 0 && (
        <Card className="mb-4">
          <CardHeader>
            <CardTitle className="text-base">Score Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {Object.entries(paper.score_breakdown).map(([key, val]) => (
                <div key={key} className="flex justify-between text-sm">
                  <span className="text-zinc-600 capitalize">{key.replace(/_/g, " ")}</span>
                  <span className="font-medium">{typeof val === "number" ? Math.round(val * 100) / 100 : val}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

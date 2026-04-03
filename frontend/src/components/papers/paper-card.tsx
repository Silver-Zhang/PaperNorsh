"use client";

import { useState } from "react";
import Link from "next/link";
import { format, parseISO } from "date-fns";
import { ExternalLink, Sparkles, ChevronDown, ChevronUp } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { InteractionButtons } from "./interaction-buttons";
import { cn } from "@/lib/utils";
import type { PaperWithScore } from "@/types";

interface PaperCardProps {
  paper: PaperWithScore;
}

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

export function PaperCard({ paper }: PaperCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [userAction, setUserAction] = useState<string | null>(paper.user_action);

  const authors = paper.authors.slice(0, 3).map((a) => a.name).join(", ");
  const hasMoreAuthors = paper.authors.length > 3;
  const displayAuthors = hasMoreAuthors ? `${authors} et al.` : authors;

  const abstract = paper.abstract ?? "";
  const shortAbstract = abstract.slice(0, 200);
  const needsExpansion = abstract.length > 200;

  return (
    <Card className="mb-4">
      <CardContent className="p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-start gap-2 mb-2">
              <span className={cn("inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold shrink-0", sourceVariant(paper.source))}>
                {paper.source}
              </span>
              {paper.relevance_score > 0 && (
                <Badge variant="outline" className="shrink-0">
                  Score: {Math.round(paper.relevance_score * 100) / 100}
                </Badge>
              )}
            </div>
            <Link
              href={`/papers/${paper.id}`}
              className="text-lg font-semibold text-zinc-900 hover:text-indigo-600 transition-colors line-clamp-2"
            >
              {paper.title}
            </Link>
            {displayAuthors && (
              <p className="text-sm text-zinc-500 mt-1">{displayAuthors}</p>
            )}
            {paper.published_date && (
              <p className="text-xs text-zinc-400 mt-0.5">
                {format(parseISO(paper.published_date), "MMM d, yyyy")}
              </p>
            )}
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <InteractionButtons
              paperId={paper.id}
              currentAction={userAction}
              onActionChange={setUserAction}
            />
            <a
              href={paper.url}
              target="_blank"
              rel="noopener noreferrer"
              className="p-1.5 rounded-md text-zinc-400 hover:text-zinc-600 hover:bg-zinc-100 transition-colors"
              title="Open paper"
            >
              <ExternalLink className="h-4 w-4" />
            </a>
          </div>
        </div>

        {abstract && (
          <div className="mt-4">
            <p className="text-sm text-zinc-600 leading-relaxed">
              {expanded ? abstract : shortAbstract}
              {needsExpansion && !expanded && "..."}
            </p>
            {needsExpansion && (
              <button
                onClick={() => setExpanded(!expanded)}
                className="mt-1 text-xs text-indigo-600 hover:underline flex items-center gap-1"
              >
                {expanded ? (
                  <>
                    <ChevronUp className="h-3 w-3" /> Show less
                  </>
                ) : (
                  <>
                    <ChevronDown className="h-3 w-3" /> Show more
                  </>
                )}
              </button>
            )}
          </div>
        )}

        {paper.ai_summary && (
          <div className="mt-4 bg-indigo-50 rounded-md p-4">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="h-4 w-4 text-indigo-600" />
              <span className="text-xs font-semibold text-indigo-700 uppercase tracking-wide">
                AI Summary
              </span>
            </div>
            <p className="text-sm text-indigo-900">{paper.ai_summary}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

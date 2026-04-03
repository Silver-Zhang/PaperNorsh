"use client";

import { PaperCard } from "./paper-card";
import type { PaperWithScore } from "@/types";

interface PaperListProps {
  papers: PaperWithScore[];
}

export function PaperList({ papers }: PaperListProps) {
  if (papers.length === 0) {
    return (
      <div className="text-center py-16 text-zinc-500">
        <p className="text-lg font-medium">No papers found</p>
        <p className="text-sm mt-1">Check back after generating a digest</p>
      </div>
    );
  }

  return (
    <div>
      {papers.map((paper) => (
        <PaperCard key={paper.id} paper={paper} />
      ))}
    </div>
  );
}

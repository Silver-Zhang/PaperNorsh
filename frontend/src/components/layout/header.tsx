"use client";

import { useState } from "react";
import { usePathname } from "next/navigation";
import { toast } from "sonner";
import { Loader2, RefreshCw } from "lucide-react";
import { digest as digestApi } from "@/lib/api";
import { Button } from "@/components/ui/button";

const pageTitles: Record<string, string> = {
  "/dashboard": "Daily Digest",
  "/saved": "Saved Papers",
  "/ignored": "Ignored Papers",
  "/settings": "Settings",
};

export function Header() {
  const pathname = usePathname();
  const [isTriggering, setIsTriggering] = useState(false);
  const title = pageTitles[pathname] ?? "PaperNosh";

  const handleTriggerDigest = async () => {
    setIsTriggering(true);
    try {
      await digestApi.triggerDigest();
      toast.success("Digest generation triggered! Check back shortly.");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to trigger digest");
    } finally {
      setIsTriggering(false);
    }
  };

  return (
    <header className="border-b border-zinc-200 px-6 py-4 bg-white flex justify-between items-center">
      <h1 className="text-xl font-semibold text-zinc-900">{title}</h1>
      <Button
        variant="outline"
        size="sm"
        onClick={handleTriggerDigest}
        disabled={isTriggering}
      >
        {isTriggering ? (
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        ) : (
          <RefreshCw className="mr-2 h-4 w-4" />
        )}
        Trigger Digest
      </Button>
    </header>
  );
}

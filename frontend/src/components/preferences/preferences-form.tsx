"use client";

import { useState, useEffect, KeyboardEvent } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { X, Loader2 } from "lucide-react";
import { preferences as preferencesApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const schema = z.object({
  keywords: z.array(z.string()),
  exclude_keywords: z.array(z.string()),
  preferred_topics: z.array(z.string()),
  follow_authors: z.array(z.string()),
  preferred_sources: z.array(z.string()),
  preferred_journals: z.array(z.string()),
  delivery_time: z.string(),
  max_papers_per_digest: z.number().min(5).max(50),
});

type FormData = z.infer<typeof schema>;

interface TagInputProps {
  tags: string[];
  onAdd: (tag: string) => void;
  onRemove: (index: number) => void;
  placeholder?: string;
}

function TagInput({ tags, onAdd, onRemove, placeholder }: TagInputProps) {
  const [inputValue, setInputValue] = useState("");

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      const val = inputValue.trim().replace(/,$/, "");
      if (val) {
        onAdd(val);
        setInputValue("");
      }
    }
  };

  return (
    <div className="border border-zinc-200 rounded-md p-2 min-h-[42px] bg-white">
      <div className="flex flex-wrap gap-1.5 mb-1">
        {tags.map((tag, i) => (
          <span
            key={i}
            className="inline-flex items-center gap-1 bg-indigo-100 text-indigo-800 text-xs px-2 py-0.5 rounded-full"
          >
            {tag}
            <button
              type="button"
              onClick={() => onRemove(i)}
              className="hover:text-indigo-600"
            >
              <X className="h-3 w-3" />
            </button>
          </span>
        ))}
      </div>
      <input
        type="text"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder ?? "Type and press Enter or comma to add"}
        className="w-full text-sm outline-none bg-transparent placeholder:text-zinc-400"
      />
    </div>
  );
}

const SOURCE_OPTIONS = ["arxiv", "openalex", "crossref"];

export function PreferencesForm() {
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const { handleSubmit, setValue, watch } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      keywords: [],
      exclude_keywords: [],
      preferred_topics: [],
      follow_authors: [],
      preferred_sources: [],
      preferred_journals: [],
      delivery_time: "08:00",
      max_papers_per_digest: 20,
    },
  });

  const formValues = watch();

  useEffect(() => {
    setIsLoading(true);
    (preferencesApi.getPreferences() as Promise<FormData>)
      .then((prefs) => {
        if (prefs) {
          Object.entries(prefs).forEach(([key, val]) => {
            setValue(key as keyof FormData, val as never);
          });
        }
      })
      .catch(() => {
        // No preferences yet, use defaults
      })
      .finally(() => setIsLoading(false));
  }, [setValue]);

  const onSubmit = async (data: FormData) => {
    setIsSaving(true);
    try {
      await preferencesApi.updatePreferences(data);
      toast.success("Preferences saved successfully!");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to save preferences");
    } finally {
      setIsSaving(false);
    }
  };

  const addTag = (field: keyof FormData, tag: string) => {
    const arr = formValues[field] as string[];
    if (!arr.includes(tag)) {
      setValue(field, [...arr, tag] as never);
    }
  };

  const removeTag = (field: keyof FormData, index: number) => {
    const arr = formValues[field] as string[];
    setValue(field, arr.filter((_, i) => i !== index) as never);
  };

  const toggleSource = (source: string) => {
    const sources = formValues.preferred_sources;
    if (sources.includes(source)) {
      setValue("preferred_sources", sources.filter((s) => s !== source));
    } else {
      setValue("preferred_sources", [...sources, source]);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Research Interests</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1">
            <Label>Keywords</Label>
            <TagInput
              tags={formValues.keywords}
              onAdd={(t) => addTag("keywords", t)}
              onRemove={(i) => removeTag("keywords", i)}
              placeholder="e.g. machine learning, transformer..."
            />
            <p className="text-xs text-zinc-400">Papers matching these keywords will be prioritized</p>
          </div>
          <div className="space-y-1">
            <Label>Exclude Keywords</Label>
            <TagInput
              tags={formValues.exclude_keywords}
              onAdd={(t) => addTag("exclude_keywords", t)}
              onRemove={(i) => removeTag("exclude_keywords", i)}
              placeholder="e.g. survey, review..."
            />
          </div>
          <div className="space-y-1">
            <Label>Preferred Topics</Label>
            <TagInput
              tags={formValues.preferred_topics}
              onAdd={(t) => addTag("preferred_topics", t)}
              onRemove={(i) => removeTag("preferred_topics", i)}
              placeholder="e.g. NLP, computer vision..."
            />
          </div>
          <div className="space-y-1">
            <Label>Follow Authors</Label>
            <TagInput
              tags={formValues.follow_authors}
              onAdd={(t) => addTag("follow_authors", t)}
              onRemove={(i) => removeTag("follow_authors", i)}
              placeholder="e.g. Yann LeCun, Geoffrey Hinton..."
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Sources &amp; Journals</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Preferred Sources</Label>
            <div className="flex gap-3">
              {SOURCE_OPTIONS.map((source) => (
                <label
                  key={source}
                  className={cn(
                    "flex items-center gap-2 px-3 py-2 border rounded-md cursor-pointer text-sm transition-colors",
                    formValues.preferred_sources.includes(source)
                      ? "border-indigo-500 bg-indigo-50 text-indigo-700"
                      : "border-zinc-200 hover:border-zinc-300"
                  )}
                >
                  <input
                    type="checkbox"
                    className="sr-only"
                    checked={formValues.preferred_sources.includes(source)}
                    onChange={() => toggleSource(source)}
                  />
                  {source}
                </label>
              ))}
            </div>
          </div>
          <div className="space-y-1">
            <Label>Preferred Journals</Label>
            <TagInput
              tags={formValues.preferred_journals}
              onAdd={(t) => addTag("preferred_journals", t)}
              onRemove={(i) => removeTag("preferred_journals", i)}
              placeholder="e.g. Nature, Science..."
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Delivery Settings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1">
            <Label htmlFor="delivery_time">Daily Delivery Time</Label>
            <Input
              id="delivery_time"
              type="time"
              value={formValues.delivery_time}
              onChange={(e) => setValue("delivery_time", e.target.value)}
              className="w-40"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="max_papers">Max Papers Per Digest</Label>
            <Input
              id="max_papers"
              type="number"
              min={5}
              max={50}
              value={formValues.max_papers_per_digest}
              onChange={(e) => setValue("max_papers_per_digest", Number(e.target.value))}
              className="w-28"
            />
            <p className="text-xs text-zinc-400">Between 5 and 50 papers per digest</p>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button type="submit" disabled={isSaving}>
          {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          Save Preferences
        </Button>
      </div>
    </form>
  );
}

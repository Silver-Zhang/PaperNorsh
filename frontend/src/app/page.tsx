"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { BookOpen, Zap, Mail, Globe } from "lucide-react";
import Link from "next/link";

export default function LandingPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && user) {
      router.replace("/dashboard");
    }
  }, [user, isLoading, router]);

  return (
    <div className="min-h-screen bg-white">
      {/* Nav */}
      <nav className="border-b border-zinc-200 px-6 py-4 flex items-center justify-between max-w-7xl mx-auto">
        <div className="flex items-center gap-2">
          <BookOpen className="h-6 w-6 text-indigo-600" />
          <span className="font-bold text-xl text-zinc-900">PaperNosh</span>
        </div>
        <div className="flex items-center gap-4">
          <Link href="/login" className="text-sm text-zinc-600 hover:text-zinc-900">
            Sign In
          </Link>
          <Link
            href="/register"
            className="text-sm bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 transition-colors"
          >
            Get Started
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-7xl mx-auto px-6 py-24 text-center">
        <div className="inline-flex items-center gap-2 bg-indigo-50 text-indigo-700 text-sm px-3 py-1 rounded-full mb-6">
          <Zap className="h-3.5 w-3.5" />
          <span>AI-powered research curation</span>
        </div>
        <h1 className="text-5xl font-bold text-zinc-900 leading-tight mb-6">
          Your Personal Research
          <br />
          <span className="text-indigo-600">Paper Feed</span>
        </h1>
        <p className="text-xl text-zinc-500 max-w-2xl mx-auto mb-10">
          Stop drowning in database searches. PaperNosh delivers the papers that matter to you, every day.
        </p>
        <div className="flex items-center justify-center gap-4">
          <Link
            href="/register"
            className="bg-indigo-600 text-white px-8 py-3 rounded-md text-base font-medium hover:bg-indigo-700 transition-colors"
          >
            Get Started Free
          </Link>
          <Link
            href="/login"
            className="border border-zinc-300 text-zinc-700 px-8 py-3 rounded-md text-base font-medium hover:bg-zinc-50 transition-colors"
          >
            Sign In
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="bg-zinc-50 py-24">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-zinc-900 text-center mb-4">
            Everything you need to stay current
          </h2>
          <p className="text-zinc-500 text-center mb-12">
            Built for researchers who care about staying ahead
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-white rounded-xl border border-zinc-200 p-6">
              <div className="h-10 w-10 bg-indigo-100 rounded-lg flex items-center justify-center mb-4">
                <Zap className="h-5 w-5 text-indigo-600" />
              </div>
              <h3 className="font-semibold text-zinc-900 mb-2">Smart Filtering</h3>
              <p className="text-zinc-500 text-sm">
                Configure keywords, authors, topics, and journals. Our AI scores each paper for relevance to your interests.
              </p>
            </div>
            <div className="bg-white rounded-xl border border-zinc-200 p-6">
              <div className="h-10 w-10 bg-indigo-100 rounded-lg flex items-center justify-center mb-4">
                <Mail className="h-5 w-5 text-indigo-600" />
              </div>
              <h3 className="font-semibold text-zinc-900 mb-2">Daily Digest</h3>
              <p className="text-zinc-500 text-sm">
                Receive a curated selection of papers at your preferred time. Never miss important research again.
              </p>
            </div>
            <div className="bg-white rounded-xl border border-zinc-200 p-6">
              <div className="h-10 w-10 bg-indigo-100 rounded-lg flex items-center justify-center mb-4">
                <Globe className="h-5 w-5 text-indigo-600" />
              </div>
              <h3 className="font-semibold text-zinc-900 mb-2">Multi-Source</h3>
              <p className="text-zinc-500 text-sm">
                Aggregates from arXiv, OpenAlex, Crossref and more. One platform for all your research sources.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-24">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-zinc-900 text-center mb-4">
            How It Works
          </h2>
          <p className="text-zinc-500 text-center mb-12">
            Up and running in minutes
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                step: "1",
                title: "Configure",
                desc: "Set your keywords, follow authors, pick your sources and schedule your daily delivery time.",
              },
              {
                step: "2",
                title: "Discover",
                desc: "PaperNosh fetches papers from multiple sources and scores them against your preferences.",
              },
              {
                step: "3",
                title: "Read",
                desc: "Review your curated digest, save papers for later, and refine your feed over time.",
              },
            ].map((item) => (
              <div key={item.step} className="text-center">
                <div className="h-12 w-12 bg-indigo-600 text-white rounded-full flex items-center justify-center text-lg font-bold mx-auto mb-4">
                  {item.step}
                </div>
                <h3 className="font-semibold text-zinc-900 mb-2">{item.title}</h3>
                <p className="text-zinc-500 text-sm">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-zinc-200 py-8">
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-indigo-600" />
            <span className="font-semibold text-zinc-900">PaperNosh</span>
          </div>
          <p className="text-sm text-zinc-400">© 2024 PaperNosh. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

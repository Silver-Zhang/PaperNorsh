export interface User {
  id: string;
  email: string;
  full_name: string;
  timezone: string;
  is_active: boolean;
  created_at: string;
}

export interface UserPreference {
  id: string;
  user_id: string;
  keywords: string[];
  exclude_keywords: string[];
  preferred_topics: string[];
  follow_authors: string[];
  preferred_sources: string[];
  preferred_journals: string[];
  delivery_time: string;
  max_papers_per_digest: number;
}

export interface Author {
  name: string;
  affiliation?: string;
}

export interface Paper {
  id: string;
  title: string;
  authors: Author[];
  abstract: string | null;
  source: string;
  source_id: string;
  doi: string | null;
  arxiv_id: string | null;
  url: string;
  published_date: string | null;
  journal_name: string | null;
  venue: string | null;
  keywords: string[];
  ai_summary: string | null;
  created_at: string;
}

export interface PaperWithScore extends Paper {
  relevance_score: number;
  score_breakdown: Record<string, number>;
  user_action: string | null;
}

export interface DigestItem {
  paper_id: string;
  relevance_score: number;
  rank: number;
}

export interface DailyDigest {
  id: string;
  user_id: string;
  date: string;
  status: string;
  papers: DigestItem[];
  email_sent_at: string | null;
  created_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}

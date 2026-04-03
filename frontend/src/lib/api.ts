const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("papernosh_token");
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (res.status === 401) {
    if (typeof window !== "undefined") {
      localStorage.removeItem("papernosh_token");
      window.location.href = "/login";
    }
    throw new Error("Unauthorized");
  }

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || "Request failed");
  }

  if (res.status === 204) return {} as T;
  return res.json();
}

export const auth = {
  login: async (email: string, password: string) => {
    const body = new URLSearchParams({ username: email, password });
    const res = await fetch(`${API_URL}/api/auth/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body.toString(),
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: "Login failed" }));
      throw new Error(error.detail || "Login failed");
    }
    return res.json();
  },
  register: async (email: string, password: string, full_name: string) =>
    request("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name }),
    }),
  me: async () => request("/api/auth/me"),
};

export const preferences = {
  getPreferences: async () => request("/api/preferences"),
  updatePreferences: async (data: unknown) =>
    request("/api/preferences", {
      method: "PUT",
      body: JSON.stringify(data),
    }),
};

export const papers = {
  listPapers: async (params: Record<string, string | number> = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params).map(([k, v]) => [k, String(v)])
    ).toString();
    return request(`/api/papers${qs ? `?${qs}` : ""}`);
  },
  getPaper: async (id: string) => request(`/api/papers/${id}`),
  interact: async (id: string, action: string) =>
    request(`/api/papers/${id}/interact`, {
      method: "POST",
      body: JSON.stringify({ action }),
    }),
  getSaved: async () => request("/api/papers/saved"),
  getIgnored: async () => request("/api/papers/ignored"),
};

export const digest = {
  getTodayDigest: async () => request("/api/digest/today"),
  getDigestHistory: async () => request("/api/digest/history"),
  triggerDigest: async () =>
    request("/api/digest/trigger", { method: "POST" }),
};

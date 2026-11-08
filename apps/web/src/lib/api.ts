import { createClient } from "@supabase/supabase-js";
import { QueryClient } from "@tanstack/react-query";
import type {
  Dashboard,
  Module,
  Concept,
  StudySession,
  Stage,
} from "../types/domain";

const url = import.meta.env.VITE_SUPABASE_URL as string | undefined;
const key = import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined;
export const supabase =
  url && key
    ? createClient(url, key, {
        auth: { flowType: "pkce", detectSessionInUrl: false },
      })
    : null;
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30000, retry: 1 },
    mutations: { retry: false },
  },
});
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}
let userPromise: Promise<{ id: string; mode: string }> | undefined;
export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-Request-ID": crypto.randomUUID(),
  };
  if (supabase) {
    const { data } = await supabase.auth.getSession();
    if (data.session)
      headers.Authorization = `Bearer ${data.session.access_token}`;
  }
  const res = await fetch(`/api/v1${path}`, {
    ...options,
    credentials: "same-origin",
    headers: { ...headers, ...options.headers },
    signal: options.signal ?? AbortSignal.timeout(15000),
  });
  const body: unknown = await res.json();
  if (!res.ok) {
    const error = body as { error?: { message?: string } };
    throw new ApiError(
      res.status,
      error.error?.message ?? "通信に失敗しました。",
    );
  }
  return body as T;
}
export function ensureUser() {
  if (!userPromise)
    userPromise = (async () => {
      if (supabase) {
        const { data } = await supabase.auth.getSession();
        if (!data.session) {
          const { error } = await supabase.auth.signInAnonymously();
          if (error) throw error;
        }
        return api<{ id: string; mode: string }>("/auth/me");
      }
      return api<{ id: string; mode: string }>("/auth/guest", {
        method: "POST",
      });
    })().catch((err) => {
      userPromise = undefined;
      throw err;
    });
  return userPromise;
}
export async function userApi<T>(path: string, options: RequestInit = {}) {
  await ensureUser();
  return api<T>(path, options);
}
export const queries = {
  dashboard: {
    queryKey: ["dashboard"],
    queryFn: () => userApi<Dashboard>("/dashboard"),
  },
  modules: {
    queryKey: ["modules"],
    queryFn: () => api<Module[]>("/modules"),
    staleTime: Infinity,
  },
  concepts: {
    queryKey: ["concepts"],
    queryFn: () => api<Concept[]>("/concepts"),
    staleTime: Infinity,
  },
};
export function problemCount(concepts: Concept[]) {
  return concepts.reduce((sum, c) => sum + (c.problem_count ?? 6), 0);
}
export async function newSession(
  options: {
    kind?: string;
    concept_id?: string;
    count?: number;
    modules?: string[];
    stages?: Stage[];
  } = {},
) {
  return userApi<StudySession>("/sessions", {
    method: "POST",
    body: JSON.stringify({ kind: "daily", ...options }),
  });
}
export function sessionPath(s: StudySession) {
  return `/drill/s/${s.id}/${s.items[s.position]?.id ?? s.items[0].id}`;
}
export function refreshLearning() {
  return queryClient.invalidateQueries({ queryKey: ["dashboard"] });
}

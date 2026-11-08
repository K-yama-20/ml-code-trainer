-- Additive: existing sessions, drafts and submission history are retained.
create table if not exists public.session_flows (
  session_id text primary key references public.study_sessions(id),
  policy jsonb not null default '{}'::jsonb,
  advances jsonb not null default '{}'::jsonb
);
alter table public.session_flows enable row level security;
-- Access is mediated by the API, which checks the session owner. No direct
-- authenticated/anonymous client policy exposes continuation state.
revoke all on public.session_flows from anon, authenticated;

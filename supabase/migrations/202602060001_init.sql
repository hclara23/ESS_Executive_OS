create extension if not exists "pgcrypto";
create extension if not exists "vector";

create schema if not exists jarvis;

create type jarvis.domain_enum as enum ('WORK', 'PERSONAL');
create type jarvis.visibility_enum as enum ('personal_private', 'business_private', 'org_shared');
create type jarvis.role_enum as enum ('owner', 'admin', 'member');
create type jarvis.task_status_enum as enum ('todo', 'in_progress', 'blocked', 'done');
create type jarvis.priority_enum as enum ('low', 'medium', 'high', 'critical');
create type jarvis.approval_status_enum as enum ('pending', 'approved', 'rejected', 'canceled');
create type jarvis.risk_enum as enum ('low', 'medium', 'high');
create type jarvis.message_channel_enum as enum ('whatsapp', 'email', 'web');
create type jarvis.message_direction_enum as enum ('inbound', 'outbound');
create type jarvis.assistant_persona_enum as enum ('alex', 'sandra');
create type jarvis.briefing_type_enum as enum ('morning', 'night');

create or replace function jarvis.current_user_id()
returns uuid
language sql
stable
as $$
  select auth.uid();
$$;

create or replace function jarvis.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create table if not exists jarvis.orgs (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists jarvis.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  org_id uuid references jarvis.orgs(id) on delete cascade,
  full_name text,
  email text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists jarvis.org_members (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references jarvis.orgs(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role jarvis.role_enum not null default 'member',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (org_id, user_id)
);

create table if not exists jarvis.assistants (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references jarvis.orgs(id) on delete cascade,
  owner_user_id uuid not null references auth.users(id) on delete cascade,
  persona jarvis.assistant_persona_enum not null,
  display_name text not null,
  domain_default jarvis.domain_enum not null default 'WORK',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (org_id, persona)
);

create table if not exists jarvis.assistant_settings (
  id uuid primary key default gen_random_uuid(),
  assistant_id uuid not null references jarvis.assistants(id) on delete cascade,
  org_id uuid not null references jarvis.orgs(id) on delete cascade,
  tone numeric not null default 0.6,
  detail numeric not null default 0.6,
  quiet_hours_start time,
  quiet_hours_end time,
  allow_personal_in_work boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (assistant_id)
);

create table if not exists jarvis.calendar_events (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references jarvis.orgs(id) on delete cascade,
  assistant_id uuid references jarvis.assistants(id) on delete set null,
  owner_user_id uuid references auth.users(id) on delete set null,
  domain jarvis.domain_enum not null default 'WORK',
  visibility jarvis.visibility_enum not null default 'org_shared',
  title text not null,
  start_at timestamptz not null,
  end_at timestamptz,
  location text,
  metadata jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists jarvis.tasks (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references jarvis.orgs(id) on delete cascade,
  assistant_id uuid references jarvis.assistants(id) on delete set null,
  owner_user_id uuid references auth.users(id) on delete set null,
  domain jarvis.domain_enum not null,
  visibility jarvis.visibility_enum not null default 'business_private',
  status jarvis.task_status_enum not null default 'todo',
  priority jarvis.priority_enum not null default 'medium',
  title text not null,
  details text,
  due_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists jarvis.approvals (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references jarvis.orgs(id) on delete cascade,
  assistant_id uuid references jarvis.assistants(id) on delete set null,
  owner_user_id uuid references auth.users(id) on delete set null,
  domain jarvis.domain_enum not null,
  visibility jarvis.visibility_enum not null default 'business_private',
  status jarvis.approval_status_enum not null default 'pending',
  risk jarvis.risk_enum not null default 'low',
  proposed_action text not null,
  result text,
  requested_by uuid references auth.users(id) on delete set null,
  approved_by uuid references auth.users(id) on delete set null,
  metadata jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists jarvis.assistant_runs (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references jarvis.orgs(id) on delete cascade,
  assistant_id uuid references jarvis.assistants(id) on delete set null,
  domain jarvis.domain_enum not null default 'WORK',
  status text not null default 'completed',
  trigger text not null default 'scheduler',
  summary text,
  metadata jsonb,
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists jarvis.assistant_plans (
  id uuid primary key default gen_random_uuid(),
  run_id uuid not null references jarvis.assistant_runs(id) on delete cascade,
  org_id uuid not null references jarvis.orgs(id) on delete cascade,
  assistant_id uuid references jarvis.assistants(id) on delete set null,
  plan_json jsonb not null,
  created_at timestamptz not null default now()
);

create table if not exists jarvis.memory_facts (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references jarvis.orgs(id) on delete cascade,
  assistant_id uuid references jarvis.assistants(id) on delete set null,
  owner_user_id uuid references auth.users(id) on delete set null,
  domain jarvis.domain_enum not null,
  visibility jarvis.visibility_enum not null default 'business_private',
  fact_type text not null,
  payload jsonb not null,
  source text,
  confidence numeric not null default 0.7,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists jarvis.memory_episodes (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references jarvis.orgs(id) on delete cascade,
  assistant_id uuid references jarvis.assistants(id) on delete set null,
  owner_user_id uuid references auth.users(id) on delete set null,
  domain jarvis.domain_enum not null,
  visibility jarvis.visibility_enum not null default 'business_private',
  summary text not null,
  metadata jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists jarvis.lessons_learned (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references jarvis.orgs(id) on delete cascade,
  assistant_id uuid references jarvis.assistants(id) on delete set null,
  owner_user_id uuid references auth.users(id) on delete set null,
  domain jarvis.domain_enum not null,
  visibility jarvis.visibility_enum not null default 'business_private',
  lesson text not null,
  created_at timestamptz not null default now()
);

create table if not exists jarvis.messages (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references jarvis.orgs(id) on delete cascade,
  assistant_id uuid references jarvis.assistants(id) on delete set null,
  owner_user_id uuid references auth.users(id) on delete set null,
  domain jarvis.domain_enum not null,
  visibility jarvis.visibility_enum not null default 'business_private',
  channel jarvis.message_channel_enum not null,
  direction jarvis.message_direction_enum not null,
  status text not null default 'queued',
  sender text,
  recipient text,
  content text not null,
  external_id text,
  metadata jsonb,
  created_at timestamptz not null default now()
);

create table if not exists jarvis.whatsapp_consent (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references jarvis.orgs(id) on delete cascade,
  owner_user_id uuid references auth.users(id) on delete set null,
  phone text not null,
  opted_in_at timestamptz not null default now(),
  opted_out_at timestamptz,
  source text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (org_id, phone)
);

create table if not exists jarvis.whatsapp_sessions (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references jarvis.orgs(id) on delete cascade,
  phone text not null,
  last_inbound_at timestamptz,
  last_outbound_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (org_id, phone)
);

create table if not exists jarvis.whatsapp_templates (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references jarvis.orgs(id) on delete cascade,
  name text not null,
  content_sid text not null,
  description text,
  status text not null default 'approved',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (org_id, name)
);

create table if not exists jarvis.kb_documents (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references jarvis.orgs(id) on delete cascade,
  assistant_id uuid references jarvis.assistants(id) on delete set null,
  owner_user_id uuid references auth.users(id) on delete set null,
  domain jarvis.domain_enum not null,
  visibility jarvis.visibility_enum not null default 'business_private',
  title text not null,
  storage_path text not null,
  mime_type text,
  size_bytes bigint,
  checksum text,
  status text not null default 'indexed',
  metadata jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists jarvis.kb_chunks (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references jarvis.orgs(id) on delete cascade,
  document_id uuid not null references jarvis.kb_documents(id) on delete cascade,
  assistant_id uuid references jarvis.assistants(id) on delete set null,
  owner_user_id uuid references auth.users(id) on delete set null,
  domain jarvis.domain_enum not null,
  visibility jarvis.visibility_enum not null default 'business_private',
  chunk_index integer not null,
  content text not null,
  token_count integer,
  metadata jsonb,
  embedding vector(1536),
  keyword_tsv tsvector generated always as (to_tsvector('english', content)) stored,
  created_at timestamptz not null default now()
);

create index if not exists kb_chunks_tsv_idx on jarvis.kb_chunks using gin (keyword_tsv);

create table if not exists jarvis.kb_tags (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references jarvis.orgs(id) on delete cascade,
  document_id uuid not null references jarvis.kb_documents(id) on delete cascade,
  tag text not null,
  created_at timestamptz not null default now()
);

create table if not exists jarvis.briefings (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references jarvis.orgs(id) on delete cascade,
  assistant_id uuid references jarvis.assistants(id) on delete set null,
  owner_user_id uuid references auth.users(id) on delete set null,
  domain jarvis.domain_enum not null,
  visibility jarvis.visibility_enum not null default 'business_private',
  briefing_type jarvis.briefing_type_enum not null,
  content jsonb not null,
  created_at timestamptz not null default now()
);

create table if not exists jarvis.audit_log (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references jarvis.orgs(id) on delete cascade,
  actor_user_id uuid references auth.users(id) on delete set null,
  action text not null,
  target_table text,
  target_id uuid,
  metadata jsonb,
  created_at timestamptz not null default now()
);

create or replace function jarvis.is_org_member(org_id uuid)
returns boolean
language sql
stable
as $$
  select exists (
    select 1 from jarvis.org_members m
    where m.org_id = org_id and m.user_id = auth.uid()
  );
$$;

create or replace function jarvis.is_org_admin(org_id uuid)
returns boolean
language sql
stable
as $$
  select exists (
    select 1 from jarvis.org_members m
    where m.org_id = org_id and m.user_id = auth.uid()
      and m.role in ('owner', 'admin')
  );
$$;

create or replace function jarvis.can_access_private(owner_user_id uuid, org_id uuid)
returns boolean
language sql
stable
as $$
  select owner_user_id = auth.uid() or jarvis.is_org_admin(org_id);
$$;

alter table jarvis.orgs enable row level security;
alter table jarvis.profiles enable row level security;
alter table jarvis.org_members enable row level security;
alter table jarvis.assistants enable row level security;
alter table jarvis.assistant_settings enable row level security;
alter table jarvis.calendar_events enable row level security;
alter table jarvis.tasks enable row level security;
alter table jarvis.approvals enable row level security;
alter table jarvis.assistant_runs enable row level security;
alter table jarvis.assistant_plans enable row level security;
alter table jarvis.memory_facts enable row level security;
alter table jarvis.memory_episodes enable row level security;
alter table jarvis.lessons_learned enable row level security;
alter table jarvis.messages enable row level security;
alter table jarvis.whatsapp_consent enable row level security;
alter table jarvis.whatsapp_sessions enable row level security;
alter table jarvis.whatsapp_templates enable row level security;
alter table jarvis.kb_documents enable row level security;
alter table jarvis.kb_chunks enable row level security;
alter table jarvis.kb_tags enable row level security;
alter table jarvis.briefings enable row level security;
alter table jarvis.audit_log enable row level security;

create policy orgs_select on jarvis.orgs for select using (jarvis.is_org_member(id));
create policy orgs_update on jarvis.orgs for update using (jarvis.is_org_admin(id));
create policy orgs_insert on jarvis.orgs for insert with check (auth.uid() is not null);

create policy profiles_select on jarvis.profiles
  for select using (jarvis.is_org_member(org_id));
create policy profiles_insert on jarvis.profiles
  for insert with check (id = auth.uid());
create policy profiles_update on jarvis.profiles
  for update using (id = auth.uid());

create policy org_members_select on jarvis.org_members
  for select using (jarvis.is_org_member(org_id));
create policy org_members_insert on jarvis.org_members
  for insert with check (jarvis.is_org_admin(org_id));
create policy org_members_update on jarvis.org_members
  for update using (jarvis.is_org_admin(org_id));
create policy org_members_delete on jarvis.org_members
  for delete using (jarvis.is_org_admin(org_id));

create policy assistants_select on jarvis.assistants
  for select using (jarvis.is_org_member(org_id));
create policy assistants_insert on jarvis.assistants
  for insert with check (jarvis.is_org_admin(org_id));
create policy assistants_update on jarvis.assistants
  for update using (jarvis.is_org_admin(org_id) or owner_user_id = auth.uid());

create policy assistant_settings_select on jarvis.assistant_settings
  for select using (jarvis.is_org_member(org_id));
create policy assistant_settings_update on jarvis.assistant_settings
  for update using (jarvis.is_org_admin(org_id) or assistant_id in (
    select id from jarvis.assistants where owner_user_id = auth.uid()
  ));

create policy calendar_events_select on jarvis.calendar_events
  for select using (
    jarvis.is_org_member(org_id)
    and (
      visibility = 'org_shared'
      or jarvis.can_access_private(owner_user_id, org_id)
    )
  );
create policy calendar_events_insert on jarvis.calendar_events
  for insert with check (
    jarvis.is_org_member(org_id)
    and (owner_user_id = auth.uid() or jarvis.is_org_admin(org_id))
  );
create policy calendar_events_update on jarvis.calendar_events
  for update using (owner_user_id = auth.uid() or jarvis.is_org_admin(org_id));

create policy tasks_select on jarvis.tasks
  for select using (
    jarvis.is_org_member(org_id)
    and (visibility = 'org_shared' or jarvis.can_access_private(owner_user_id, org_id))
  );
create policy tasks_insert on jarvis.tasks
  for insert with check (
    jarvis.is_org_member(org_id)
    and (owner_user_id = auth.uid() or jarvis.is_org_admin(org_id))
  );
create policy tasks_update on jarvis.tasks
  for update using (owner_user_id = auth.uid() or jarvis.is_org_admin(org_id));

create policy approvals_select on jarvis.approvals
  for select using (
    jarvis.is_org_member(org_id)
    and (visibility = 'org_shared' or jarvis.can_access_private(owner_user_id, org_id))
  );
create policy approvals_insert on jarvis.approvals
  for insert with check (jarvis.is_org_member(org_id));
create policy approvals_update on jarvis.approvals
  for update using (jarvis.is_org_admin(org_id) or owner_user_id = auth.uid());

create policy assistant_runs_select on jarvis.assistant_runs
  for select using (jarvis.is_org_member(org_id));
create policy assistant_runs_insert on jarvis.assistant_runs
  for insert with check (jarvis.is_org_member(org_id));

create policy assistant_plans_select on jarvis.assistant_plans
  for select using (jarvis.is_org_member(org_id));
create policy assistant_plans_insert on jarvis.assistant_plans
  for insert with check (jarvis.is_org_member(org_id));

create policy memory_facts_select on jarvis.memory_facts
  for select using (
    jarvis.is_org_member(org_id)
    and (visibility = 'org_shared' or jarvis.can_access_private(owner_user_id, org_id))
  );
create policy memory_facts_insert on jarvis.memory_facts
  for insert with check (
    jarvis.is_org_member(org_id)
    and (owner_user_id = auth.uid() or jarvis.is_org_admin(org_id))
  );
create policy memory_facts_update on jarvis.memory_facts
  for update using (owner_user_id = auth.uid() or jarvis.is_org_admin(org_id));

create policy memory_episodes_select on jarvis.memory_episodes
  for select using (
    jarvis.is_org_member(org_id)
    and (visibility = 'org_shared' or jarvis.can_access_private(owner_user_id, org_id))
  );
create policy memory_episodes_insert on jarvis.memory_episodes
  for insert with check (
    jarvis.is_org_member(org_id)
    and (owner_user_id = auth.uid() or jarvis.is_org_admin(org_id))
  );
create policy memory_episodes_update on jarvis.memory_episodes
  for update using (owner_user_id = auth.uid() or jarvis.is_org_admin(org_id));

create policy lessons_select on jarvis.lessons_learned
  for select using (
    jarvis.is_org_member(org_id)
    and (visibility = 'org_shared' or jarvis.can_access_private(owner_user_id, org_id))
  );
create policy lessons_insert on jarvis.lessons_learned
  for insert with check (
    jarvis.is_org_member(org_id)
    and (owner_user_id = auth.uid() or jarvis.is_org_admin(org_id))
  );

create policy messages_select on jarvis.messages
  for select using (
    jarvis.is_org_member(org_id)
    and (visibility = 'org_shared' or jarvis.can_access_private(owner_user_id, org_id))
  );
create policy messages_insert on jarvis.messages
  for insert with check (jarvis.is_org_member(org_id));

create policy whatsapp_consent_select on jarvis.whatsapp_consent
  for select using (jarvis.is_org_admin(org_id) or owner_user_id = auth.uid());
create policy whatsapp_consent_insert on jarvis.whatsapp_consent
  for insert with check (jarvis.is_org_admin(org_id) or owner_user_id = auth.uid());
create policy whatsapp_consent_update on jarvis.whatsapp_consent
  for update using (jarvis.is_org_admin(org_id) or owner_user_id = auth.uid());

create policy whatsapp_sessions_select on jarvis.whatsapp_sessions
  for select using (jarvis.is_org_admin(org_id));
create policy whatsapp_sessions_insert on jarvis.whatsapp_sessions
  for insert with check (jarvis.is_org_admin(org_id));
create policy whatsapp_sessions_update on jarvis.whatsapp_sessions
  for update using (jarvis.is_org_admin(org_id));

create policy whatsapp_templates_select on jarvis.whatsapp_templates
  for select using (jarvis.is_org_admin(org_id));
create policy whatsapp_templates_insert on jarvis.whatsapp_templates
  for insert with check (jarvis.is_org_admin(org_id));
create policy whatsapp_templates_update on jarvis.whatsapp_templates
  for update using (jarvis.is_org_admin(org_id));

create policy kb_documents_select on jarvis.kb_documents
  for select using (
    jarvis.is_org_member(org_id)
    and (visibility = 'org_shared' or jarvis.can_access_private(owner_user_id, org_id))
  );
create policy kb_documents_insert on jarvis.kb_documents
  for insert with check (
    jarvis.is_org_member(org_id)
    and (owner_user_id = auth.uid() or jarvis.is_org_admin(org_id))
  );
create policy kb_documents_update on jarvis.kb_documents
  for update using (owner_user_id = auth.uid() or jarvis.is_org_admin(org_id));

create policy kb_chunks_select on jarvis.kb_chunks
  for select using (
    jarvis.is_org_member(org_id)
    and (visibility = 'org_shared' or jarvis.can_access_private(owner_user_id, org_id))
  );
create policy kb_chunks_insert on jarvis.kb_chunks
  for insert with check (
    jarvis.is_org_member(org_id)
    and (owner_user_id = auth.uid() or jarvis.is_org_admin(org_id))
  );

create policy kb_tags_select on jarvis.kb_tags
  for select using (jarvis.is_org_member(org_id));
create policy kb_tags_insert on jarvis.kb_tags
  for insert with check (jarvis.is_org_member(org_id));

create policy briefings_select on jarvis.briefings
  for select using (
    jarvis.is_org_member(org_id)
    and (visibility = 'org_shared' or jarvis.can_access_private(owner_user_id, org_id))
  );
create policy briefings_insert on jarvis.briefings
  for insert with check (jarvis.is_org_member(org_id));

create policy audit_log_select on jarvis.audit_log
  for select using (jarvis.is_org_admin(org_id));
create policy audit_log_insert on jarvis.audit_log
  for insert with check (jarvis.is_org_member(org_id));

create trigger set_updated_at_orgs before update on jarvis.orgs
  for each row execute function jarvis.set_updated_at();
create trigger set_updated_at_profiles before update on jarvis.profiles
  for each row execute function jarvis.set_updated_at();
create trigger set_updated_at_org_members before update on jarvis.org_members
  for each row execute function jarvis.set_updated_at();
create trigger set_updated_at_assistants before update on jarvis.assistants
  for each row execute function jarvis.set_updated_at();
create trigger set_updated_at_assistant_settings before update on jarvis.assistant_settings
  for each row execute function jarvis.set_updated_at();
create trigger set_updated_at_calendar_events before update on jarvis.calendar_events
  for each row execute function jarvis.set_updated_at();
create trigger set_updated_at_tasks before update on jarvis.tasks
  for each row execute function jarvis.set_updated_at();
create trigger set_updated_at_approvals before update on jarvis.approvals
  for each row execute function jarvis.set_updated_at();
create trigger set_updated_at_memory_facts before update on jarvis.memory_facts
  for each row execute function jarvis.set_updated_at();
create trigger set_updated_at_memory_episodes before update on jarvis.memory_episodes
  for each row execute function jarvis.set_updated_at();
create trigger set_updated_at_whatsapp_consent before update on jarvis.whatsapp_consent
  for each row execute function jarvis.set_updated_at();
create trigger set_updated_at_whatsapp_sessions before update on jarvis.whatsapp_sessions
  for each row execute function jarvis.set_updated_at();
create trigger set_updated_at_whatsapp_templates before update on jarvis.whatsapp_templates
  for each row execute function jarvis.set_updated_at();
create trigger set_updated_at_kb_documents before update on jarvis.kb_documents
  for each row execute function jarvis.set_updated_at();

insert into storage.buckets (id, name, public)
values ('kb-documents', 'kb-documents', false)
on conflict (id) do nothing;

create policy "KB documents access" on storage.objects
for select to authenticated
using (bucket_id = 'kb-documents');

create policy "KB documents insert" on storage.objects
for insert to authenticated
with check (bucket_id = 'kb-documents');

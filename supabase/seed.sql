with first_user as (
  select id, email from auth.users order by created_at asc limit 1
),
new_org as (
  insert into jarvis.orgs (name)
  select 'Electric Supply Source'
  where exists (select 1 from first_user)
  returning id
)
insert into jarvis.org_members (org_id, user_id, role)
select new_org.id, first_user.id, 'owner'
from new_org, first_user;

insert into jarvis.profiles (id, org_id, full_name, email)
select first_user.id, orgs.id, 'Alex Sanchez', first_user.email
from first_user
join jarvis.org_members on jarvis.org_members.user_id = first_user.id
join jarvis.orgs on jarvis.orgs.id = jarvis.org_members.org_id;

with org as (
  select org_id from jarvis.org_members order by created_at asc limit 1
),
owner as (
  select user_id from jarvis.org_members order by created_at asc limit 1
)
insert into jarvis.assistants (org_id, owner_user_id, persona, display_name)
select org.org_id, owner.user_id, 'alex', 'Alex Sanchez'
from org, owner
union all
select org.org_id, owner.user_id, 'sandra', 'Sandra Sanchez'
from org, owner;

insert into jarvis.assistant_settings (assistant_id, org_id, tone, detail, allow_personal_in_work)
select id, org_id, 0.6, 0.6, false from jarvis.assistants;

insert into jarvis.whatsapp_templates (org_id, name, content_sid, description)
select org_id, 'approval_request', 'HXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX', 'Request approval for action'
from jarvis.orgs
on conflict do nothing;

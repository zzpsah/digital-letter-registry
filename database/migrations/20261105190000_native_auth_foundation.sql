-- Native DLR identity/session foundation.
-- CUTOVER ONLY: apply after native auth is deployed and traffic is drained.
-- This migration copies existing GoTrue identities without changing UUIDs or
-- password hashes. It intentionally does NOT drop auth.users or its triggers;
-- those are removed only after all application/RPC references are migrated.

BEGIN;

CREATE TABLE IF NOT EXISTS public.app_users (
    id uuid PRIMARY KEY,
    email text,
    password_hash text,
    password_scheme text NOT NULL DEFAULT 'bcrypt',
    email_verified_at timestamptz,
    is_disabled boolean NOT NULL DEFAULT false,
    app_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    user_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    last_login_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS app_users_email_lower_uidx
    ON public.app_users (lower(email)) WHERE email IS NOT NULL;

ALTER TABLE public.app_users ADD COLUMN IF NOT EXISTS google_subject text;
CREATE UNIQUE INDEX IF NOT EXISTS app_users_google_subject_uidx
    ON public.app_users (google_subject) WHERE google_subject IS NOT NULL;

CREATE TABLE IF NOT EXISTS public.app_sessions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES public.app_users(id) ON DELETE CASCADE,
    refresh_token_hash text NOT NULL UNIQUE,
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL,
    revoked_at timestamptz,
    last_used_at timestamptz,
    user_agent text,
    ip_address inet
);
CREATE INDEX IF NOT EXISTS app_sessions_user_active_idx
    ON public.app_sessions (user_id, expires_at DESC)
    WHERE revoked_at IS NULL;

CREATE TABLE IF NOT EXISTS public.app_email_tokens (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES public.app_users(id) ON DELETE CASCADE,
    token_hash text NOT NULL UNIQUE,
    purpose text NOT NULL CHECK (purpose IN ('verify_email', 'password_reset', 'magic_link')),
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL,
    consumed_at timestamptz
);
CREATE INDEX IF NOT EXISTS app_email_tokens_pending_idx
    ON public.app_email_tokens (user_id, purpose, expires_at)
    WHERE consumed_at IS NULL;

-- The native FastAPI service may SET ROLE to the same RLS-bound roles as PostgREST.
GRANT authenticated, anon TO dlr_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.app_users, public.app_sessions, public.app_email_tokens TO dlr_app;

-- Preserve every existing account ID and bcrypt password hash.
INSERT INTO public.app_users (
    id, email, password_hash, password_scheme, email_verified_at,
    is_disabled, app_metadata, user_metadata, last_login_at, created_at, updated_at
)
SELECT
    u.id,
    lower(u.email),
    NULLIF(u.encrypted_password, ''),
    'bcrypt',
    COALESCE(u.email_confirmed_at, u.confirmed_at),
    (u.deleted_at IS NOT NULL OR (u.banned_until IS NOT NULL AND u.banned_until > now())),
    COALESCE(u.raw_app_meta_data, '{}'::jsonb),
    COALESCE(u.raw_user_meta_data, '{}'::jsonb),
    u.last_sign_in_at,
    COALESCE(u.created_at, now()),
    COALESCE(u.updated_at, now())
FROM auth.users AS u
ON CONFLICT (id) DO UPDATE SET
    email = EXCLUDED.email,
    password_hash = EXCLUDED.password_hash,
    email_verified_at = EXCLUDED.email_verified_at,
    is_disabled = EXCLUDED.is_disabled,
    app_metadata = EXCLUDED.app_metadata,
    user_metadata = EXCLUDED.user_metadata,
    last_login_at = EXCLUDED.last_login_at,
    updated_at = EXCLUDED.updated_at;

-- Keep the native identity copy synchronized while the old auth gateway is drained.
CREATE OR REPLACE FUNCTION public.sync_native_app_user_from_auth()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
  INSERT INTO public.app_users(
    id,email,password_hash,password_scheme,email_verified_at,is_disabled,
    app_metadata,user_metadata,last_login_at,created_at,updated_at
  ) VALUES (
    NEW.id,lower(NEW.email),NULLIF(NEW.encrypted_password,''),'bcrypt',
    COALESCE(NEW.email_confirmed_at,NEW.confirmed_at),
    (NEW.deleted_at IS NOT NULL OR (NEW.banned_until IS NOT NULL AND NEW.banned_until > now())),
    COALESCE(NEW.raw_app_meta_data,'{}'::jsonb),COALESCE(NEW.raw_user_meta_data,'{}'::jsonb),
    NEW.last_sign_in_at,COALESCE(NEW.created_at,now()),COALESCE(NEW.updated_at,now())
  ) ON CONFLICT(id) DO UPDATE SET
    email=excluded.email,password_hash=excluded.password_hash,password_scheme='bcrypt',
    email_verified_at=excluded.email_verified_at,is_disabled=excluded.is_disabled,
    app_metadata=excluded.app_metadata,user_metadata=excluded.user_metadata,
    last_login_at=excluded.last_login_at,updated_at=excluded.updated_at;
  RETURN NEW;
END;
$$;
DROP TRIGGER IF EXISTS a_sync_native_app_user_after_auth_write ON auth.users;
CREATE TRIGGER a_sync_native_app_user_after_auth_write
AFTER INSERT OR UPDATE ON auth.users
FOR EACH ROW EXECUTE FUNCTION public.sync_native_app_user_from_auth();
CREATE OR REPLACE FUNCTION public.disable_native_app_user_after_auth_delete()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
  UPDATE public.app_users SET is_disabled=true,updated_at=now() WHERE id=OLD.id;
  UPDATE public.app_sessions SET revoked_at=now() WHERE user_id=OLD.id AND revoked_at IS NULL;
  RETURN OLD;
END;
$$;
DROP TRIGGER IF EXISTS z_disable_native_app_user_after_auth_delete ON auth.users;
CREATE TRIGGER z_disable_native_app_user_after_auth_delete
AFTER DELETE ON auth.users
FOR EACH ROW EXECUTE FUNCTION public.disable_native_app_user_after_auth_delete();


-- Repoint all public foreign keys while preserving the existing user UUIDs.
DO $$ DECLARE fk record; rewritten text; BEGIN
  FOR fk IN SELECT conrelid::regclass AS table_name, conname, pg_get_constraintdef(oid) AS definition
    FROM pg_constraint WHERE contype='f' AND confrelid='auth.users'::regclass AND connamespace='public'::regnamespace
  LOOP
    rewritten := replace(fk.definition,'REFERENCES auth.users','REFERENCES public.app_users');
    EXECUTE format('ALTER TABLE %s DROP CONSTRAINT %I',fk.table_name,fk.conname);
    EXECUTE format('ALTER TABLE %s ADD CONSTRAINT %I %s NOT VALID',fk.table_name,fk.conname,rewritten);
    EXECUTE format('ALTER TABLE %s VALIDATE CONSTRAINT %I',fk.table_name,fk.conname);
  END LOOP;
END $$;


-- Trusted SECURITY DEFINER entry points keep account lifecycle operations
-- atomic while ordinary API traffic continues to use authenticated/anon RLS.
CREATE OR REPLACE FUNCTION public.dlr_native_complete_approved_account(
    target_email text, target_password_hash text, target_password_scheme text,
    target_approval_token uuid
) RETURNS uuid
LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
DECLARE req public.account_access_requests%rowtype;
DECLARE target_user_id uuid;
BEGIN
    SELECT * INTO req FROM public.account_access_requests
    WHERE email=lower(btrim(target_email)) AND approval_token=target_approval_token
      AND status='approved' AND approved_role IS NOT NULL
      AND approved_at >= now() - interval '7 days'
    ORDER BY approved_at DESC LIMIT 1 FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'invalid or expired approval'; END IF;

    SELECT id INTO target_user_id FROM public.app_users
    WHERE lower(email)=lower(btrim(target_email)) LIMIT 1 FOR UPDATE;
    IF target_user_id IS NULL THEN target_user_id := gen_random_uuid(); END IF;

    INSERT INTO public.app_users(id,email,password_hash,password_scheme,email_verified_at,is_disabled,updated_at)
    VALUES(target_user_id,lower(btrim(target_email)),target_password_hash,target_password_scheme,now(),false,now())
    ON CONFLICT(id) DO UPDATE SET email=excluded.email,password_hash=excluded.password_hash,
      password_scheme=excluded.password_scheme,email_verified_at=now(),is_disabled=false,updated_at=now();

    INSERT INTO public.archive_members(archive_id,user_id,role,status,updated_at)
    VALUES(req.archive_id,target_user_id,req.approved_role,'active',now())
    ON CONFLICT(archive_id,user_id) DO UPDATE SET role=excluded.role,status='active',updated_at=now();

    UPDATE public.account_access_requests SET status='completed',completed_at=now(),
      approval_token=NULL,updated_at=now() WHERE id=req.id AND status='approved';
    RETURN target_user_id;
END;
$$;

CREATE OR REPLACE FUNCTION public.dlr_native_register_with_invite(
    target_email text, target_password_hash text, target_password_scheme text,
    target_invite_code uuid
) RETURNS TABLE(user_id uuid, archive_role text)
LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
DECLARE invite public.archive_member_invites%rowtype;
DECLARE new_user_id uuid;
BEGIN
    SELECT i.* INTO invite FROM public.archive_member_invites i
    JOIN public.archives a ON a.id=i.archive_id
    WHERE i.email=lower(btrim(target_email)) AND i.invite_code=target_invite_code
      AND i.status='pending' AND a.status='active'
    LIMIT 1 FOR UPDATE OF i;
    IF NOT FOUND THEN RAISE EXCEPTION 'invalid invitation'; END IF;
    IF EXISTS(SELECT 1 FROM public.app_users WHERE lower(email)=lower(btrim(target_email))) THEN
      RAISE EXCEPTION 'account already exists';
    END IF;
    new_user_id := gen_random_uuid();
    INSERT INTO public.app_users(id,email,password_hash,password_scheme,email_verified_at,is_disabled)
    VALUES(new_user_id,lower(btrim(target_email)),target_password_hash,target_password_scheme,now(),false);
    INSERT INTO public.archive_members(archive_id,user_id,role,status)
    VALUES(invite.archive_id,new_user_id,invite.role,'active');
    UPDATE public.archive_member_invites SET status='accepted',accepted_user_id=new_user_id,
      accepted_at=now(),updated_at=now() WHERE id=invite.id AND status='pending';
    RETURN QUERY SELECT new_user_id, invite.role;
END;
$$;

CREATE OR REPLACE FUNCTION public.dlr_native_link_google_identity(
    target_email text, target_google_subject text
) RETURNS uuid
LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
DECLARE target_user_id uuid;
DECLARE linked_subject text;
BEGIN
    SELECT id,google_subject INTO target_user_id,linked_subject
    FROM public.app_users
    WHERE lower(email)=lower(btrim(target_email)) AND email_verified_at IS NOT NULL AND NOT is_disabled
    LIMIT 1 FOR UPDATE;
    IF target_user_id IS NULL THEN RAISE EXCEPTION 'Google sign-in is not enabled for this account'; END IF;
    IF NOT EXISTS(SELECT 1 FROM public.archive_members WHERE user_id=target_user_id AND status='active') THEN
      RAISE EXCEPTION 'active archive membership required';
    END IF;
    IF linked_subject IS NOT NULL AND linked_subject <> target_google_subject THEN
      RAISE EXCEPTION 'a different Google identity is already linked';
    END IF;
    UPDATE public.app_users SET google_subject=target_google_subject,last_login_at=now(),updated_at=now()
    WHERE id=target_user_id;
    RETURN target_user_id;
END;
$$;

REVOKE ALL ON FUNCTION public.dlr_native_link_google_identity(text,text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.dlr_native_link_google_identity(text,text) TO dlr_app;

CREATE OR REPLACE FUNCTION public.dlr_native_admin_user_account_action(
    caller_id uuid, target_archive_id uuid, target_user_id uuid,
    action_name text, new_password_hash text DEFAULT NULL,
    new_password_scheme text DEFAULT 'argon2'
) RETURNS boolean
LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
DECLARE caller_role text;
DECLARE target_role text;
DECLARE target_status text;
BEGIN
    SELECT role INTO caller_role FROM public.archive_members
    WHERE archive_id=target_archive_id AND user_id=caller_id AND status='active' FOR UPDATE;
    IF caller_role IS DISTINCT FROM 'admin' THEN RAISE EXCEPTION 'admin access required'; END IF;
    SELECT role,status INTO target_role,target_status FROM public.archive_members
    WHERE archive_id=target_archive_id AND user_id=target_user_id FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'user not found'; END IF;

    IF action_name='reset_password' THEN
      IF new_password_hash IS NULL THEN RAISE EXCEPTION 'password hash required'; END IF;
      UPDATE public.app_users SET password_hash=new_password_hash,
        password_scheme=new_password_scheme,updated_at=now() WHERE id=target_user_id;
      UPDATE public.app_sessions SET revoked_at=now()
        WHERE user_id=target_user_id AND revoked_at IS NULL;
      RETURN true;
    ELSIF action_name='delete_user' THEN
      IF caller_id=target_user_id THEN RAISE EXCEPTION 'cannot delete own admin account'; END IF;
      IF target_role='admin' AND target_status='active' AND
        (SELECT count(*) FROM public.archive_members WHERE archive_id=target_archive_id
          AND role='admin' AND status='active') <= 1 THEN
        RAISE EXCEPTION 'cannot delete the last active admin';
      END IF;
      UPDATE public.archive_members SET status='disabled',updated_at=now()
        WHERE archive_id=target_archive_id AND user_id=target_user_id;
      UPDATE public.app_users SET is_disabled=true,updated_at=now() WHERE id=target_user_id;
      UPDATE public.app_sessions SET revoked_at=now()
        WHERE user_id=target_user_id AND revoked_at IS NULL;
      RETURN true;
    ELSE
      RAISE EXCEPTION 'unsupported account action';
    END IF;
END;
$$;

REVOKE ALL ON FUNCTION public.dlr_native_complete_approved_account(text,text,text,uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.dlr_native_register_with_invite(text,text,text,uuid) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.dlr_native_admin_user_account_action(uuid,uuid,uuid,text,text,text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.dlr_native_complete_approved_account(text,text,text,uuid) TO dlr_app;
GRANT EXECUTE ON FUNCTION public.dlr_native_register_with_invite(text,text,text,uuid) TO dlr_app;
GRANT EXECUTE ON FUNCTION public.dlr_native_admin_user_account_action(uuid,uuid,uuid,text,text,text) TO dlr_app;



-- Rebind account administration RPCs to the native identity table.
create or replace function public.dlr_invite_archive_member(
  target_archive_id uuid,
  target_email text,
  target_role text
)
returns table (
  invite_id uuid,
  email text,
  role text,
  status text,
  invite_code uuid,
  user_id uuid
)
language plpgsql
security definer
set search_path = ''
as $$
declare
  normalized_email text := lower(btrim(target_email));
  matched_user_id uuid;
  result_invite public.archive_member_invites%rowtype;
  existing_role text;
begin
  if (select private.archive_member_role(target_archive_id)) is distinct from 'admin' then
    raise exception 'archive admin required';
  end if;
  if length(normalized_email) not between 3 and 320
     or position('@' in normalized_email) <= 1 then
    raise exception 'valid email required';
  end if;
  if target_role not in ('admin','editor','viewer') then
    raise exception 'invalid archive role';
  end if;

  select u.id
    into matched_user_id
  from public.app_users u
  where lower(u.email) = normalized_email
    and u.email_verified_at is not null
  order by u.created_at
  limit 1;

  if matched_user_id is not null then
    select m.role
      into existing_role
    from public.archive_members m
    where m.archive_id = target_archive_id
      and m.user_id = matched_user_id;

    if existing_role is null then
      insert into public.archive_members (
        archive_id, user_id, role, status
      )
      values (
        target_archive_id, matched_user_id, target_role, 'active'
      );
    end if;

    insert into public.archive_member_invites (
      archive_id,
      email,
      role,
      status,
      invited_by,
      accepted_user_id,
      accepted_at
    )
    values (
      target_archive_id,
      normalized_email,
      coalesce(existing_role, target_role),
      'accepted',
      (select auth.uid()),
      matched_user_id,
      now()
    )
    on conflict on constraint archive_member_invites_archive_id_email_key
    do update set
      role = excluded.role,
      status = 'accepted',
      invited_by = excluded.invited_by,
      accepted_user_id = excluded.accepted_user_id,
      accepted_at = excluded.accepted_at,
      updated_at = now()
    returning * into result_invite;
  else
    insert into public.archive_member_invites (
      archive_id,
      email,
      role,
      status,
      invite_code,
      invited_by,
      accepted_user_id,
      accepted_at
    )
    values (
      target_archive_id,
      normalized_email,
      target_role,
      'pending',
      extensions.gen_random_uuid(),
      (select auth.uid()),
      null,
      null
    )
    on conflict on constraint archive_member_invites_archive_id_email_key
    do update set
      role = excluded.role,
      status = 'pending',
      invite_code = excluded.invite_code,
      invited_by = excluded.invited_by,
      accepted_user_id = null,
      accepted_at = null,
      updated_at = now()
    returning * into result_invite;
  end if;

  return query
  select
    result_invite.id,
    result_invite.email,
    result_invite.role,
    result_invite.status,
    result_invite.invite_code,
    result_invite.accepted_user_id;
end
$$;

revoke all on function public.dlr_invite_archive_member(uuid, text, text)
  from public;
revoke all on function public.dlr_invite_archive_member(uuid, text, text)
  from anon;
grant execute on function public.dlr_invite_archive_member(uuid, text, text)
  to authenticated;

create or replace function public.dlr_list_archive_access(
  target_archive_id uuid
)
returns table (
  kind text,
  record_id uuid,
  user_id uuid,
  email text,
  role text,
  status text,
  invite_code uuid,
  created_at timestamptz
)
language plpgsql
stable
security definer
set search_path = ''
as $$
begin
  if (select private.archive_member_role(target_archive_id)) is distinct from 'admin' then
    raise exception 'archive admin required';
  end if;

  return query
  select
    'member'::text,
    m.user_id,
    m.user_id,
    lower(u.email),
    m.role,
    m.status,
    null::uuid,
    m.created_at
  from public.archive_members m
  join public.app_users u on u.id = m.user_id
  where m.archive_id = target_archive_id

  union all

  select
    'invite'::text,
    i.id,
    i.accepted_user_id,
    i.email,
    i.role,
    i.status,
    case when i.status = 'pending' then i.invite_code else null::uuid end,
    i.created_at
  from public.archive_member_invites i
  where i.archive_id = target_archive_id
    and i.status <> 'accepted'

  order by created_at;
end
$$;

revoke all on function public.dlr_list_archive_access(uuid) from public;
revoke all on function public.dlr_list_archive_access(uuid) from anon;
grant execute on function public.dlr_list_archive_access(uuid)
  to authenticated;

create or replace function public.dlr_update_archive_member(
  target_archive_id uuid,
  target_user_id uuid,
  target_role text,
  target_status text
)
returns table (
  user_id uuid,
  email text,
  role text,
  status text
)
language plpgsql
security definer
set search_path = ''
as $$
begin
  if (select private.archive_member_role(target_archive_id)) is distinct from 'admin' then
    raise exception 'archive admin required';
  end if;
  if target_role not in ('admin','editor','viewer') then
    raise exception 'invalid archive role';
  end if;
  if target_status not in ('active','disabled') then
    raise exception 'invalid member status';
  end if;

  update public.archive_members m
  set role = target_role,
      status = target_status,
      updated_at = now()
  where m.archive_id = target_archive_id
    and m.user_id = target_user_id;

  if not found then
    raise exception 'archive member not found';
  end if;

  return query
  select
    m.user_id,
    lower(u.email),
    m.role,
    m.status
  from public.archive_members m
  join public.app_users u on u.id = m.user_id
  where m.archive_id = target_archive_id
    and m.user_id = target_user_id;
end
$$;

revoke all on function public.dlr_update_archive_member(uuid, uuid, text, text)
  from public;
revoke all on function public.dlr_update_archive_member(uuid, uuid, text, text)
  from anon;
grant execute on function public.dlr_update_archive_member(uuid, uuid, text, text)
  to authenticated;

COMMIT;

-- Keep the soft-delete flag and its audit metadata in sync.
-- The API search RPC already excludes is_trashed=true rows; this trigger makes
-- that predicate reliable even if a client updates only one trash field.

BEGIN;

-- Reconcile legacy/partially-written trash state before enforcing the invariant.
UPDATE public.letters
SET trashed_at = COALESCE(trashed_at, updated_at, created_at, now())
WHERE COALESCE(is_trashed, false) = true
  AND trashed_at IS NULL;

UPDATE public.letters
SET is_trashed = true
WHERE COALESCE(is_trashed, false) = false
  AND trashed_at IS NOT NULL;

UPDATE public.letters
SET trashed_by = NULL
WHERE COALESCE(is_trashed, false) = false
  AND trashed_at IS NULL
  AND trashed_by IS NOT NULL;

CREATE OR REPLACE FUNCTION public.sync_letter_trash_state()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = public
AS $function$
BEGIN
  IF TG_OP = 'INSERT' THEN
    IF COALESCE(NEW.is_trashed, false) THEN
      NEW.is_trashed := true;
      NEW.trashed_at := COALESCE(NEW.trashed_at, now());
    ELSE
      NEW.is_trashed := false;
      NEW.trashed_at := NULL;
      NEW.trashed_by := NULL;
    END IF;
    RETURN NEW;
  END IF;

  -- An explicit flag change is authoritative (delete/restore endpoints).
  IF NEW.is_trashed IS DISTINCT FROM OLD.is_trashed THEN
    IF COALESCE(NEW.is_trashed, false) THEN
      NEW.is_trashed := true;
      NEW.trashed_at := COALESCE(NEW.trashed_at, OLD.trashed_at, now());
    ELSE
      NEW.is_trashed := false;
      NEW.trashed_at := NULL;
      NEW.trashed_by := NULL;
    END IF;
  -- Also support clients that only set/clear the timestamp.
  ELSIF NEW.trashed_at IS DISTINCT FROM OLD.trashed_at THEN
    IF NEW.trashed_at IS NULL THEN
      NEW.is_trashed := false;
      NEW.trashed_by := NULL;
    ELSE
      NEW.is_trashed := true;
    END IF;
  -- Clearing the actor and timestamp together is also a restore signal.
  ELSIF NEW.trashed_by IS DISTINCT FROM OLD.trashed_by
        AND NEW.trashed_by IS NULL
        AND NEW.trashed_at IS NULL THEN
    NEW.is_trashed := false;
  END IF;

  RETURN NEW;
END;
$function$;

DROP TRIGGER IF EXISTS letters_sync_trash_state ON public.letters;
CREATE TRIGGER letters_sync_trash_state
BEFORE INSERT OR UPDATE OF is_trashed, trashed_at, trashed_by
ON public.letters
FOR EACH ROW
EXECUTE FUNCTION public.sync_letter_trash_state();

DO $constraint$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid = 'public.letters'::regclass
      AND conname = 'letters_trash_state_consistent'
  ) THEN
    ALTER TABLE public.letters
      ADD CONSTRAINT letters_trash_state_consistent
      CHECK (COALESCE(is_trashed, false) = (trashed_at IS NOT NULL))
      NOT VALID;
  END IF;
END;
$constraint$;

ALTER TABLE public.letters VALIDATE CONSTRAINT letters_trash_state_consistent;
COMMIT;

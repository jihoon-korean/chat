-- Stage61 chat2 ONLY. Run manually as database administrator AFTER two test accounts are email-verified.
-- NEVER run against production chat. Replace both placeholders with actual chat2 auth.users UUIDs.
-- This is NOT an RPC, and is NOT callable by client-side users.
-- All-or-nothing transaction. Idempotent: refuses wallets that have already received any balance.
BEGIN;
DO $$
DECLARE
  ids uuid[] := ARRAY[
    '00000000-0000-0000-0000-000000000001'::uuid,
    '00000000-0000-0000-0000-000000000002'::uuid
  ];
  uid uuid;
  mail text;
  confirmed timestamptz;
  balance_before integer;
BEGIN
  IF current_database() IS NULL THEN RAISE EXCEPTION 'DB_UNAVAILABLE'; END IF;
  IF array_length(ids,1)<>2 OR ids[1]=ids[2] THEN RAISE EXCEPTION 'TWO_DISTINCT_USERS_REQUIRED'; END IF;
  IF '00000000-0000-0000-0000-000000000001'::uuid=ANY(ids)
     OR '00000000-0000-0000-0000-000000000002'::uuid=ANY(ids) THEN
    RAISE EXCEPTION 'REPLACE_TEST_USER_IDS_FIRST';
  END IF;
  FOREACH uid IN ARRAY ids LOOP
    SELECT email,email_confirmed_at INTO mail,confirmed FROM auth.users WHERE id=uid;
    IF mail IS NULL OR confirmed IS NULL THEN RAISE EXCEPTION 'VERIFIED_TEST_USER_REQUIRED: %',uid; END IF;
    -- Verify the email addresses and test account ownership before running this script.
    INSERT INTO public.mb_wallets(user_id,balance) VALUES(uid,0) ON CONFLICT(user_id) DO NOTHING;
    SELECT balance INTO balance_before FROM public.mb_wallets WHERE user_id=uid FOR UPDATE;
    IF balance_before<>0 THEN RAISE EXCEPTION 'WALLET_NOT_ZERO: %',uid; END IF;
    IF EXISTS(SELECT 1 FROM public.mb61_point_ledger WHERE owner_id=uid) THEN
      RAISE EXCEPTION 'PREVIOUS_LEDGER_EXISTS: %',uid;
    END IF;
    UPDATE public.mb_wallets SET balance=500,updated_at=now() WHERE user_id=uid;
    RAISE NOTICE 'chat2 test wallet credited: %',uid;
  END LOOP;
END $$;
COMMIT;

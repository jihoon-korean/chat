# MEETBRIDGE Stage61 — chat2 actual browser E2E checklist

Scope: **dev/stage61-chat2-persona-chat** and Supabase **chat2** (`tifofrfxbddbxcrfisxr`) only.
Never deploy to `main` or modify production Supabase `chat` (`jxoyctdxmkezudrtfpxk`).

## Prerequisites
1. Host the development branch in an isolated preview environment with HTTPS. The current GitHub source link is **not** a live hosted app.
2. Confirm `index.html` can load `./dev/multi-profile-chat2.html` and its relative adapter `./mb61-chat2-adapter.js`. Ensure the preview is not the public production domain.
3. Use two separate, real test mailboxes and two separate browser profiles/incognito sessions. Do **not** reuse production credentials.
4. In the embedded chat2 screen, use **테스트 계정 가입** for each account, complete email confirmation if requested, then log in with the two different credentials. Record the two `auth.users.id` UUIDs in the **chat2** project only.
5. In the Supabase dashboard, confirm both test accounts have `email_confirmed_at` set and are owned by the tester. Do not bypass email verification or write passwords to SQL/GitHub.
6. After confirming the selected Supabase project is **chat2**, replace ONLY the two UUID placeholders in `dev/stage61-test-credit.sql`, run once as database administrator in chat2, and verify each test wallet shows 500P. The script refuses unconfirmed users, nonzero balances, and existing chat/ledger activity. Never expose it as a client RPC.

## E2E test sequence
- A creates persona A1; B creates persona B1; each sees only own personas under "내 멀티 프로필". The other user's nickname should appear under "대화 상대 선택".
- A sends a first message to B1. The server requests explicit 100P confirmation; cancel once and confirm wallet remains 500P. Retry, confirm, and check wallet A = 400P, B = 500P.
- Confirm B sees exactly one message in the room. Repeat the **same request ID** via a controlled dev-only test (not a new UI click) and verify the message count and wallet balance remain unchanged. Do not infer idempotency from two distinct UI sends.
- B leaves the room. A's send is blocked; wallet A stays 400P.
- B rejoins and confirms 100P. B wallet = 400P. Repeat the same rejoin request ID and verify no further deduction.
- B sends another message in the active room; no additional 100P should be charged.
- Change selected persona/peer while a charge confirmation is open; ensure the old confirmation cannot be used.
- Refresh the page and log out/in; balances and messages persist, with separate auth storage from production.
- Regression: legacy MEETBRIDGE chat tab, chat history, sending, and navigation remain unchanged.

## Acceptance and evidence
Capture timestamp, dev commit SHA, chat2 project ID, browser version, 2 account UUIDs (never passwords), wallet before/after, room ID, message IDs, request IDs, and screenshot/log for each case. Mark tests PASS only when **actually observed** in the browser. If the preview is unavailable, mark as BLOCKED; server-side SQL tests do not count as browser E2E.

## Deployment gate
Do not merge to main or modify production chat. After all tests pass, provide a test report and ask for **explicit production deployment approval**.

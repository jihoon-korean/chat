# MEETBRIDGE chat2-only HTTPS preview

## Safe isolation
- Source repo: jihoon-korean/chat
- Source branch: dev/stage61-chat2-persona-chat ONLY
- Supabase: chat2 (tifofrfxbddbxcrfisxr) ONLY
- Static publish directory: dev
- Preview entry: dev/index.html -> dev/multi-profile-chat2.html
- Never publish repository root: root index.html contains the existing production app.
- Never merge into main or change production Supabase chat (jxoyctdxmkezudrtfpxk).

## Hosting configuration (manual setup required)
Use a NEW, separately named Cloudflare Pages project or equivalent static HTTPS host. Connect only the development branch, leave the build command empty (plain static files), and set the output directory to dev. Confirm the deployed site serves only dev/index.html, dev/multi-profile-chat2.html and dev/mb61-chat2-adapter.js, NOT the repository-root index.html. Restrict access to authorized testers using host-level access control before sharing any URL. The noindex tag is not an access-control mechanism.

The project has not been deployed by the assistant. Host connection and HTTPS URL must be confirmed independently.

## Auth and payment
Two test mailboxes must be accessible to the tester. Sign up from the chat2 preview, verify the email if required, and sign in. Do not store passwords in the repository. Confirm both users' email_confirmed_at in chat2 Auth. Use dev/stage61-test-credit.sql manually with the two verified chat2 UUIDs after checking the correct project is selected. Never make this SQL a public RPC.

## Verification
Follow dev/STAGE61-E2E-CHECKLIST.md. Record actual browser evidence; SQL rollback tests are not browser verification.

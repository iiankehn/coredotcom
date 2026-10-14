# CORE automatic social publishing

Draft implementation for publishing newly added `posts/*.html` on Bluesky, Threads, and X after a push to `main`.

## Secrets required
- `BLUESKY_HANDLE`, `BLUESKY_APP_PASSWORD` (Bluesky app password)
- `THREADS_USER_ID`, `THREADS_ACCESS_TOKEN` (Threads publishing permissions and long-lived token)
- `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET` (X user-context write access)

Configure these in repository Settings → Secrets and variables → Actions. Do not commit credentials.

## Safety
The workflow is proposed on a feature branch; it will not automatically post until merged to main and credentials are provided. Manual workflow dispatch defaults to dry-run. The posting ledger is `.github/social-published.json`. Missing credentials skip the corresponding network.

## Behavior and limitations
- Automatic runs use newly **added** HTML article files, not edits or deletes.
- Manual dry-runs preview unposted articles; non-dry manual runs can backfill any article not yet recorded.
- Social API permissions, limits, media support, and account status must be verified before enabling.
- Publishing is not transactional across providers. Review the ledger and workflow logs after partial failures before retrying.
- X and Threads currently publish text and a link; Bluesky adds an external preview and attempts a thumbnail.
- Platform integration tests with authorized accounts remain outstanding.

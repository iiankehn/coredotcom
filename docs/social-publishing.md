# CORE social publishing

Status: draft, live publishing disabled. No accounts are connected until credentials are configured and authentication tests pass. Mock tests are not provider validation.

## Credentials (owner action required)

Open repository Settings → Secrets and variables → Actions → New repository secret.
Paste credentials directly into GitHub, never into chat, source files, workflow inputs, or logs.

| Service | Secret | Value |
| --- | --- | --- |
| Bluesky | `BLUESKY_HANDLE` | Full handle of the account that should publish |
| Bluesky | `BLUESKY_APP_PASSWORD` | Dedicated app password named CORE Actions, without DM access |
| Threads | `THREADS_USER_ID` | ID returned by the authorized Threads account's `/me` endpoint |
| Threads | `THREADS_ACCESS_TOKEN` | Long-lived Threads user token with `threads_basic` and `threads_content_publish` |
| X | `X_API_KEY` | App consumer/API key |
| X | `X_API_SECRET` | App consumer/API secret |
| X | `X_ACCESS_TOKEN` | User access token for the publishing account |
| X | `X_ACCESS_TOKEN_SECRET` | Matching user token secret |

Bluesky: Settings → Privacy and security → App passwords. Generate a dedicated password; do not use the account password. Current client targets accounts hosted on bsky.social; other PDS hosts need a reviewed client change.

Threads: in Meta for Developers, use an app with the Threads API use case. Add your account as a tester if using development mode, accept the invitation through Threads, authorize the two scopes above, obtain a user token and exchange it for a long-lived token through the official tools. Record its expiry and replace the GitHub secret before expiry. This draft does not automatically refresh the token. Read validation verifies identity, not publishing permission.

X: use your developer app's OAuth 1.0a user credentials, configured for Read and Write. Generate user tokens after enabling write access. A bearer/app-only token does not replace the four secrets. API access and quota must permit the calls; no subscriptions or spending are configured by this implementation.

Official references:
- https://docs.bsky.app/docs/tutorials/creating-a-post
- https://developers.facebook.com/docs/threads/get-started/get-access-tokens-and-permissions
- https://developers.facebook.com/docs/threads/get-started/long-lived-tokens
- https://www.postman.com/meta/threads/collection/dht3nzz/threads-api
- https://docs.x.com/fundamentals/authentication/oauth-1-0a/obtaining-user-access-tokens

## Validation and activation

1. Keep this PR draft while reviewing and configuring credentials. Push/PR checks run without secrets and without posting.
2. To make GitHub's manual dispatch available, merge the reviewed workflow into `main` with `SOCIAL_PUBLISH_ENABLED` absent or `false`. Merging alone does not enable posting. The integrations job is blocked on all ordinary pushes while this variable is absent/false.
3. Actions → CORE social publishing → Run workflow → `validate`. This authenticates Bluesky and reads account identity on Threads and X. It creates no public posts. Confirm the returned accounts are the intended ones.
4. Run `test` separately for each platform with a unique alphanumeric ID, such as `bsky20261014`, `threads20261014`, and `x20261014`. This sends exactly one labeled CORE integration test linking the homepage, never an existing article. Reusing an ID prevents duplicate tests. Verify each post on the service. Public test posts are not deleted automatically; remove them manually if desired.
5. Only after all checks and three real publication tests pass, record the current main SHA in repository variable `SOCIAL_ACTIVATION_SHA`, then set `SOCIAL_PUBLISH_ENABLED=true`. The script requires successful test entries for all services, validates accounts before live writes, and rejects old push events whose base predates the activation SHA. Activation is intentionally a separate step and has not been performed.

## Delivery and recovery

Only files added under `posts/*.html` in a subsequent main push qualify. Existing articles are frozen in `.github/social-baseline.json`; edits, deletes, and manual dispatch never backfill them. If articles are published while posting is disabled, they are not replayed when enabled. Successful posting is recorded per platform.

The runner commits and pushes a `pending` record BEFORE a write, then commits the provider ID after success. A failed state push prevents the corresponding write. Pending entries block automatic retry, because a timeout can occur after the provider accepted a post. Inspect the service and replace pending with its actual ID/status if delivered; otherwise remove the pending entry only after verifying it was not delivered. This favors avoiding duplicate public posts over automatic retries. Cross-platform publication is not transactional. A failure in one platform does not retract others. New pushes can advance main during posting; if a state commit conflicts, reconcile rather than force-push.

Tokens travel in authorization headers (Bluesky password only in its session request body). HTTP redirects are refused. Exceptions do not print request URLs, headers, response bodies, tokens, or session JWTs. Actions are pinned to commit SHAs; PR tests have read-only permissions and receive no credentials. Integration writes use the built-in GitHub token, not a stored GitHub personal access token. Repository writers can modify workflows to access repository secrets; restrict repository write access appropriately.

Output is text plus full article URL. Bluesky includes an external link card without an uploaded thumbnail. Threads and X rely on the site's link preview. This avoids the draft's broken image fetch and hardcoded image content type. Long titles are conservatively shortened to meet Unicode limits and preserve the complete link.

Run offline regression checks: `python -m unittest discover -s tests -v`.

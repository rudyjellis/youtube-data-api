# Setup: Desktop OAuth (`diger-youtube`)

This kit uses a **Google Cloud Desktop** OAuth client in the **`diger-youtube`** project.
Secrets live in **Doppler** (names only in brand YAML). Never commit client secrets,
refresh tokens, or `tokens/*.token.json`.

## 1. GCP project

1. Open [Google Cloud Console](https://console.cloud.google.com/) → project **`diger-youtube`**.
2. Enable **YouTube Data API v3** (APIs & Services → Library).
3. Configure the **OAuth consent screen**:
   - User type: **External** (unless you have a Workspace-only constraint).
   - App name / support email as appropriate for Diger Studios.
   - Scopes used by this kit:
     - `https://www.googleapis.com/auth/youtube`
     - `https://www.googleapis.com/auth/youtube.upload`
     - `https://www.googleapis.com/auth/youtube.force-ssl`
   - Publishing status: leave in **Testing** until verified.
   - **Test users**: add **`ops@unboundceo.com`** (and any other operators who will run `auth-login`).

## 2. Create a Desktop OAuth client

1. APIs & Services → Credentials → **Create credentials** → **OAuth client ID**.
2. Application type: **Desktop app**.
3. Name e.g. `youtube-data-api-desktop`.
4. Download the JSON if you want a local bootstrap file — **do not commit it**.
   Prefer storing values in Doppler (next step).

## 3. Doppler secrets (names referenced by brand YAML)

Create Doppler project **`youtube-data-api`** (configs `dev`/`prd`). Brand YAML points at project + config.

| Secret name (store the *value* in Doppler) | Purpose |
| --- | --- |
| `YOUTUBE_OAUTH_CLIENT_ID` | Desktop client ID |
| `YOUTUBE_OAUTH_CLIENT_SECRET` | Desktop client secret |
| `YOUTUBE_OAUTH_REFRESH_TOKEN` | Long-lived refresh token from `auth-login` |

Brand files under `brands/` reference these **names only** — never paste values into git.

Example for Unbound CEO (`brands/unboundceo.yaml`):

- Doppler project: `diger-youtube`
- Doppler config: `unboundceo`
- Channel ID: `UCwt4BI86Ovzi0eUtv0cs--w`

Optional: export the same names as env vars for local runs without the Doppler CLI.

## 4. First interactive login (as the ops test user)

Sign in as **`ops@unboundceo.com`** (must be on the consent screen test-user list)
and complete Desktop OAuth:

```bash
pip install -e .
# Ensure Doppler (or env) has CLIENT_ID + CLIENT_SECRET for the brand config
youtube-data-api --brand unboundceo auth-login
```

This writes a **gitignored** token cache under `tokens/`. Copy the refresh token
into Doppler as `YOUTUBE_OAUTH_REFRESH_TOKEN` for that brand config, then agents
can run non-interactively.

## 5. Verify

```bash
youtube-data-api --brand unboundceo list --max-results 5
```

## Safety: never auto-Public

- Uploads default to **Unlisted** (`privacy_status: unlisted` in brand defaults).
- Setting `public` requires an explicit `--allow-public` flag on `upload` / `update`.
- Do not change the kit to publish publicly by default.

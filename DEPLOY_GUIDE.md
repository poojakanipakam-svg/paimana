# Deploying PAIMANA — Hugging Face Spaces (free, recommended)

The included zip `paimana_huggingface_deploy.zip` contains everything the
Space needs: Dockerfile, README.md (Space metadata), backend/ (app code,
trained models, SQLite DB, built frontend), data/ (panel CSV + manifest).

## Steps (~10 minutes, free)

1. Create a free account at https://huggingface.co (if you don't have one).

2. Go to https://huggingface.co/new-space
   - Owner: your username
   - Space name: paimana
   - SDK: **Docker**  (leave "Blank template")
   - Space hardware: **CPU basic — 2 vCPU, 16GB RAM (Free)**
   - Visibility: Public (needed for the link to open without login)

3. Upload the files. Easiest way — git:
   ```bash
   git clone https://huggingface.co/spaces/<your-username>/paimana
   cd paimana
   # unzip paimana_huggingface_deploy.zip here so that Dockerfile,
   # README.md, backend/, data/ sit at the repo root, then:
   git add .
   git commit -m "PAIMANA deploy"
   git push
   ```
   (No git? In the Space page use "Files" tab -> "Add file" -> upload each
   file; folders can be dragged into the web file browser.)

4. Wait for the build (~5–10 min: installing the ML libraries).
   Watch the "Logs" / "Building" tab.

5. When it shows "Running", your app is live at:
   https://<your-username>-paimana.hf.space
   (API docs: https://<your-username>-paimana.hf.space/docs)

## Notes
- Free Spaces sleep after ~48h of inactivity; the first request after sleep
  takes ~30–60s to wake. For the SIH demo, open the link 2 minutes early.
- To update: edit files and push again — Docker layer cache makes rebuilds fast.
- Space storage limit (20GB) and RAM (16GB) are far above PAIMANA's needs.

# Alternative hosts (same Dockerfile)

- Render (render.com): New -> Web Service -> "Deploy an existing image /
  Docker" -> point it at this repo (Dockerfile auto-detected). Free tier
  sleeps after 15 min idle (~50s cold start).
- Railway / Fly.io / Koyeb: all run the same Dockerfile; set PORT if the
  platform requires it (the Dockerfile already respects $PORT).
- Vercel / Netlify: NOT suitable for the backend (serverless size limit
  ~250MB unzipped; the ML stack unpacks to 500MB+; ephemeral filesystem).

# For SIH judging

Local demo (run_windows.bat) is the most reliable — no internet needed.
Use the hosted link as a backup and for the submission deck.

# Railway.com deployment (uses the SAME zip)

The `paimana_huggingface_deploy.zip` also works on Railway — it contains a
`Dockerfile` at the repo root, which Railway auto-detects.

IMPORTANT: do NOT upload the *website* zip (paimana_website.zip) to Railway.
Its root has no app entry point and Railway's auto-builder fails with
"Config Error / could not determine how to build the project".

## Steps
1. Unzip `paimana_huggingface_deploy.zip`. The root must contain:
   Dockerfile, README.md, requirements.txt, start.sh, backend/, data/
2. Push those contents to your GitHub repo (replace the old files).
3. Railway rebuilds automatically: it detects the Dockerfile - no
   Root Directory or start command configuration needed.
   The container listens on Railway's $PORT automatically.
4. When the deploy shows "Success": Settings -> Networking ->
   Generate Domain to get your public URL.
5. If the container restarts (out of memory): Settings -> Deploy ->
   Resources and raise Memory to 2 GB. PAIMANA needs more than the
   512 MB default because of the ML libraries.

## Cost note
Railway's $5 credit is a ONE-TIME trial (not a recurring free tier).
When it runs out the service stops. For a permanently free deployment,
use Hugging Face Spaces (top of this guide) with the same zip.

## Troubleshooting: site loads but every page shows "HTTP 500"

Symptom: the PAIMANA header/sidebar render fine, but Dashboard / Projects /
Trends show an "HTTP 500" error.

Cause: the deployed GitHub repo is missing `backend/data/paimana.db`
(the SQLite database). This usually happens because a `.gitignore` rule
(ex. `*.db`) or an interrupted web upload dropped it. The page chrome comes
from files, so it renders; every data endpoint hits the missing DB and fails.

Confirm in 30 seconds: open the repo on GitHub -> `backend/data/` ->
`paimana.db` should be listed (about 7.5 MB). Railway logs (Deployments ->
View Logs) will show `sqlite3.OperationalError: no such table: panel`.

Fix (self-healing start.sh - recommended):
1. Open `start.sh` at the repo root -> click the pencil (Edit) -> replace
   the whole file with the new version shipped in this package -> Commit.
2. Railway redeploys automatically. Watch the deploy logs - you will see:
   `[start] database missing/empty - rebuilding from bundled panel...`
   followed by a ~1-2 min retrain, then
   `[start] rebuild complete - 11,121 panel rows, 2,163 scored projects`.
3. Reload the site - all pages now show data.

The new start.sh heals BOTH common gaps at container start: missing models
(retrains) and missing/empty database (rebuilds from the bundled CSV), so a
complete deploy no longer depends on every binary file surviving the upload.

Alternative quick fix: upload `backend/data/paimana.db` directly - in GitHub,
navigate to `backend/data/` -> Add file -> Upload files -> drop `paimana.db`
-> Commit. (Web uploads bypass .gitignore.) Railway redeploys automatically.

If instead nothing loads at all, see the memory note above (2 GB) and check
the deploy logs for a Python traceback.

## Troubleshooting: only Dashboard & Projects show "HTTP 500"

Symptom: header, filters, Data & Sources, Trends and Model Performance all
work, but Dashboard and Projects return HTTP 500 (everything else fine).

Cause: the container is missing `libgomp1`. The lightgbm/xgboost wheels link
against the SYSTEM libgomp, which `python:3.12-slim` does not include. Then
`import lightgbm` fails, start.sh mistakes the bundled models for broken ones,
starts a retrain that wipes the database and crashes at the same import -
leaving the `panel` table intact but `project_scores` empty. Dashboard and
Projects are exactly the two endpoints that read `project_scores`.

Confirm: Railway logs (Deployments -> View Logs) will show
`libgomp.so.1: cannot open shared object file`.

Fix (already in this package): the Dockerfile now runs
`apt-get install -y libgomp1` before pip install, and start.sh backs up the
database before any rebuild and restores it if the rebuild fails. If your
repo predates this fix, replace `Dockerfile` and `start.sh` at the repo root
with the versions from this package and let Railway redeploy. Expected log
line on a healthy start:
`[start] all good - 11,121 panel rows, 2,163 scored projects, models loadable`

## Optional: Gemini-powered assistant (database-grounded)

The Assistant page can answer through Google Gemini instead of the built-in
rule-based engine - but strictly grounded: Gemini must CALL PAIMANA's database
tools (function calling) for every fact, so it cannot invent numbers. If no
key is configured, the API fails, or traffic exceeds the built-in rate limit
(30 requests/min), the deterministic engine answers automatically. The badge
under each answer shows which engine replied.

### Enabling it
1. Create a FREE API key at https://aistudio.google.com/apikey
   (Google AI Studio; the free tier has daily quotas).
2. Where to put the key:
   - ONLINE (Railway / HF Spaces): as an environment variable - never in the
     GitHub repo (the repo is public).
     * Railway: service -> Variables -> New Variable ->
       Name `GEMINI_API_KEY`, Value = your key. Railway redeploys automatically.
     * Hugging Face Spaces: Settings -> Variables and secrets ->
       New SECRET `GEMINI_API_KEY`.
   - LAPTOP: open the `.env` file at the package root (shipped with a blank
     placeholder) and paste the key after `GEMINI_API_KEY=`, then restart the
     app. The `.gitignore` excludes `.env` from git; still keep it empty when
     uploading files to GitHub via the web UI.
   Environment variables always take priority over the `.env` file.
3. Ask the assistant something. The badge under the answer should read
   "answered by gemini-3.5-flash - facts retrieved from the PAIMANA database
   (tool-grounded)". If it says "built-in deterministic engine", the variable
   is not set (check spelling: GEMINI_API_KEY).

### Optional settings
- `GEMINI_MODEL` - model id (default `gemini-3.5-flash`). Any current Gemini
  API model id works, e.g. `gemini-3.7-flash`.

### Design notes (for the judges)
- Every number is fetched live from SQLite via tool functions; the system
  prompt forbids inventing facts and requires "Insufficient data available
  for this analysis." when tools cannot answer.
- The rule-based engine remains as a zero-dependency fallback, so the
  assistant works even with no key, no quota or no network to Google.
- The assistant ONLY answers PAIMANA questions: an off-topic guard
  (vocabulary filter) refuses unrelated questions before any engine is
  invoked, and the Gemini system prompt enforces the same restriction
  as a second line of defense.

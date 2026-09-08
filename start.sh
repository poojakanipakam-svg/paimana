#!/bin/sh
# PAIMANA self-healing start (Railway / Hugging Face / Render / local Docker).
#
# The bundled models and database are used as-is when they are healthy.
# If either is missing or not loadable, the full pipeline is re-run from
# the bundled dataset (~1-2 min). The existing database is backed up first
# and restored if the rebuild fails, so a failed retrain can never leave
# the app worse off than it started.

cd "$(cd "$(dirname "$0")" && pwd)/backend" || exit 1

python - <<'EOF'
import os, shutil, sqlite3, subprocess, sys


def db_counts():
    conn = sqlite3.connect('data/paimana.db')
    try:
        panel = conn.execute('SELECT COUNT(*) FROM panel').fetchone()[0]
        scores = conn.execute('SELECT COUNT(*) FROM project_scores').fetchone()[0]
        return panel, scores
    finally:
        conn.close()


def db_ok():
    try:
        panel, scores = db_counts()
        return panel > 0 and scores > 0
    except Exception:
        return False


def models_ok():
    try:
        import joblib
        joblib.load('artifacts/models.joblib')
        return True
    except Exception as e:
        print(f'[start] models not loadable: {e!r}')
        return False


def heal(reason):
    if not os.path.exists('../data/paimana_panel.csv'):
        print('[start] ERROR: data/paimana_panel.csv not found in the repo - '
              'the upload is incomplete. Push the data/ folder, then redeploy.')
        return
    print(f'[start] {reason} - rebuilding from bundled panel '
          '(retrain + rescore, takes a few minutes)...')
    backup = None
    if os.path.exists('data/paimana.db'):
        backup = 'data/paimana.db.bak'
        shutil.copy('data/paimana.db', backup)
    r = subprocess.run([sys.executable, '-m', 'app.ml.pipeline'])
    if r.returncode == 0 and db_ok():
        panel, scores = db_counts()
        print(f'[start] rebuild complete - {panel:,} panel rows, '
              f'{scores:,} scored projects')
        if backup:
            os.remove(backup)
    else:
        print(f'[start] rebuild FAILED (exit code {r.returncode})')
        if backup:
            shutil.move(backup, 'data/paimana.db')
            print('[start] previous database restored - starting server with it')


models = models_ok()
db = db_ok()
if models and db:
    panel, scores = db_counts()
    print(f'[start] all good - {panel:,} panel rows, {scores:,} scored projects, '
          'models loadable')
else:
    heal('database missing or empty' if not db else 'models not loadable')
EOF

exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-7860}"

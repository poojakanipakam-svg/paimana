"""Optional Gemini-powered assistant layer (database-grounded, no hallucinated facts).

If the GEMINI_API_KEY environment variable is set, questions are answered by
Gemini (default: gemini-3.5-flash) through FUNCTION CALLING: the model may only
obtain facts by calling PAIMANA's tool functions, which run live SQL against the
SQLite panel. If the key is absent, the API fails, or anything goes wrong, the
deterministic rule-based engine in assistant.py answers instead - so the
feature is strictly additive and the site never breaks.

The API key is read from (in order of priority): 1) the GEMINI_API_KEY
environment variable (Railway / HF Spaces Variables), 2) a `.env` file at the
package root or in backend/ (for laptop use - fill in `.env`, never commit a
real key to a public repo). The key is never stored in the code.

References: Gemini API function calling,
https://ai.google.dev/gemini-api/docs/generate-content/function-calling
"""
import json
import os
import time
import urllib.error
import urllib.request
from collections import deque

from ..config import ARTIFACTS_DIR, DATA_DIR, MANIFEST_JSON
from ..db import query_df
from .assistant import INSUFFICIENT, _find_project, _latest_scores

API_URL = ('https://generativelanguage.googleapis.com/v1beta/models/'
           '{model}:generateContent')
DEFAULT_MODEL = 'gemini-3.5-flash'
MAX_TOOL_ROUNDS = 6
HTTP_TIMEOUT = 25

SYSTEM_PROMPT = """You are the PAIMANA assistant: an analytics assistant over
India's MoSPI central-sector infrastructure project panel (public government
data, parsed from QPISR and Flash report PDFs).

STRICT RULES:
1. Obtain EVERY fact by calling the provided tools. Never invent, estimate or
   remember numbers. If no tool provides the answer, reply exactly:
   "Insufficient data available for this analysis."
2. Answer only from the tool results shown in this conversation.
3. Amounts are in Indian rupee crore. Percentages are as returned by tools.
4. Always state the report month the data refers to (e.g. "as of 2025-03").
5. The implementation-risk score is a transparent, configurable monitoring aid
   computed by PAIMANA - NEVER describe it as an official government rating,
   decision or prediction of what the government will do.
6. Be concise: at most ~150 words. Use short lists for project rankings.
7. TOPIC RESTRICTION: you answer ONLY questions about PAIMANA and its data -
   MoSPI central-sector infrastructure projects, cost/schedule overruns, risk
   scores, warnings, sectors/ministries/states, the predictive models, the
   dashboard and the data sources. For ANY other question (general knowledge,
   coding, maths, jokes, current events, personal questions) reply exactly:
   "I can only answer questions about PAIMANA - MoSPI central-sector
   infrastructure projects." followed by one example question. Never answer
   an off-topic question, not even partially."""


# --------------------------------------------------------------------------
# configuration: real environment variables win over the .env file
# --------------------------------------------------------------------------
def _env_file_values():
    """Parse KEY=VALUE pairs from an optional .env file (package root,
    backend/ or the working directory). Missing files are simply skipped."""
    here = os.path.dirname(os.path.abspath(__file__))    # .../backend/app/services
    candidates = [
        os.path.join(here, '..', '..', '..', '.env'),    # package root/.env
        os.path.join(here, '..', '..', '.env'),          # backend/.env
        os.path.join(os.getcwd(), '.env'),
        os.path.join(os.getcwd(), '..', '.env'),
    ]
    values = {}
    for path in candidates:
        try:
            if not os.path.isfile(path):
                continue
            with open(path, encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#') or '=' not in line:
                        continue
                    key, _, val = line.partition('=')
                    key, val = key.strip(), val.strip().strip('"').strip("'")
                    if key and key not in values:
                        values[key] = val
        except OSError:
            continue
    return values


def get_setting(name: str) -> str:
    """Setting lookup: real environment variable first (Railway/HF Variables),
    then the .env file (laptop use)."""
    v = os.environ.get(name)
    if v:
        return v
    return _env_file_values().get(name, '')


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def enabled() -> bool:
    return bool(get_setting('GEMINI_API_KEY'))


def _clean(obj):
    """Recursively convert pandas/numpy values into JSON-safe python."""
    import math
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if obj is None:
        return None
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if hasattr(obj, 'item'):          # numpy scalar
        try:
            return _clean(obj.item())
        except Exception:
            return str(obj)
    if isinstance(obj, (int, float, str, bool)):
        return obj
    return str(obj)


_calls = deque()          # timestamps of recent gemini calls (rate guard)


def _rate_ok(limit=30, window=60):
    now = time.time()
    while _calls and now - _calls[0] > window:
        _calls.popleft()
    if len(_calls) >= limit:
        return False
    _calls.append(now)
    return True


def _ongoing():
    s = _latest_scores()
    return s[s['event'] != 'completed']


def _match(df, col, val):
    """Case-insensitive scope matching: exact, then substring (so
    'railways' matches 'MINISTRY OF RAILWAYS')."""
    v = str(val).lower().strip()
    m = df[col].astype(str).str.lower() == v
    if not m.any():
        m = df[col].astype(str).str.lower().str.contains(v, regex=False, na=False)
    return df[m] if m.any() else df.iloc[0:0]


# --------------------------------------------------------------------------
# tool implementations (live SQL over the panel)
# --------------------------------------------------------------------------
def _t_overview():
    panel = query_df('SELECT * FROM panel')
    months = sorted(panel['report_month'].unique())
    latest = months[-1]
    o = _ongoing()
    over = o[o['cost_overrun_pct'] > 0]
    tor = o[o['time_overrun_months'] > 0]
    return _clean({
        'report_month': latest,
        'months_covered': months,
        'ongoing_projects': int(o['project_code'].nunique()),
        'cost_overrun_projects': int(len(over)),
        'cost_overrun_share_pct': float(100 * len(over) / max(1, len(o))),
        'avg_cost_overrun_pct': float(over['cost_overrun_pct'].mean()),
        'schedule_overrun_projects': int(len(tor)),
        'schedule_overrun_share_pct': float(100 * len(tor) / max(1, len(o))),
        'avg_schedule_overrun_months': float(tor['time_overrun_months'].mean()),
        'total_original_cost_cr': float(o['original_cost'].sum()),
        'total_latest_cost_cr': float(o['latest_cost'].sum()),
        'total_expenditure_cr': float(o['cumulative_expenditure'].sum()),
        'risk_distribution': o['risk_level'].value_counts().to_dict(),
    })


def _t_top_risk(n=10, sector=None, ministry=None, state=None):
    o = _ongoing()
    if sector:
        o = _match(o, 'sector', sector)
    if ministry:
        o = _match(o, 'ministry', ministry)
    if state:
        o = _match(o, 'state', state)
    n = max(1, min(int(n or 10), 25))
    t = o.nlargest(n, 'risk_total')
    rows = [{
        'project_code': r.project_code,
        'project_name': str(r.project_name)[:70],
        'sector': r.sector,
        'state': r.state,
        'risk_score': round(float(r.risk_total), 1),
        'risk_level': r.risk_level,
        'cost_overrun_pct': r.cost_overrun_pct,
        'time_overrun_months': r.time_overrun_months,
        'model_overrun_probability': round(
            float(r.pred_prob_monitoring or 0), 3),
    } for _, r in t.iterrows()]
    return _clean({'report_month': str(o['report_month'].max()),
                   'count': len(rows), 'projects': rows})


def _t_find_project(query):
    code = _find_project(query)
    if not code:
        return {'found': False, 'note': 'No project matched; suggest using '
                'the project code shown on the Projects page.'}
    s = _latest_scores()
    r = s[s['project_code'] == code]
    if not len(r):
        return {'found': False}
    r = r.iloc[0]
    w = query_df('SELECT warning_type, severity, what, reason, action '
                 'FROM warnings WHERE project_code = ?', (code,))
    return _clean({
        'found': True, 'project_code': code,
        'project_name': r.project_name, 'sector': r.sector,
        'ministry': r.ministry, 'state': r.state,
        'original_cost_cr': r.original_cost, 'latest_cost_cr': r.latest_cost,
        'cumulative_expenditure_cr': r.cumulative_expenditure,
        'physical_progress_pct': r.physical_progress_pct,
        'cost_overrun_pct': r.cost_overrun_pct,
        'time_overrun_months': r.time_overrun_months,
        'risk_score': round(float(r.risk_total), 1), 'risk_level': r.risk_level,
        'model_overrun_probability': round(
            float(r.pred_prob_monitoring or 0), 3),
        'active_warnings': w.head(5).to_dict('records'),
    })


def _t_aggregate(sector=None, ministry=None, state=None):
    o = _ongoing()
    scope = {}
    for key, val in (('sector', sector), ('ministry', ministry),
                     ('state', state)):
        if val:
            o = _match(o, key, val)
            scope[key] = val
    if not len(o):
        return {'found': False, 'note': 'No ongoing projects match that '
                'sector/ministry/state. Valid values are listed by the '
                'get_filter_values tool.'}
    over = o[o['cost_overrun_pct'] > 0]
    tor = o[o['time_overrun_months'] > 0]
    return _clean({
        'found': True, 'scope': scope,
        'report_month': str(o['report_month'].max()),
        'ongoing_projects': int(o['project_code'].nunique()),
        'cost_overrun_projects': int(len(over)),
        'cost_overrun_share_pct': float(100 * len(over) / len(o)),
        'avg_cost_overrun_pct': float(over['cost_overrun_pct'].mean()),
        'schedule_overrun_projects': int(len(tor)),
        'avg_schedule_overrun_months': float(
            tor['time_overrun_months'].mean()),
        'total_original_cost_cr': float(o['original_cost'].sum()),
        'total_latest_cost_cr': float(o['latest_cost'].sum()),
        'top_3_riskiest': [{
            'project_code': r.project_code,
            'name': str(r.project_name)[:60],
            'risk': round(float(r.risk_total), 1),
        } for _, r in o.nlargest(3, 'risk_total').iterrows()],
    })


def _t_filter_values():
    p = query_df('SELECT DISTINCT sector, ministry, state FROM panel')
    return {
        'sectors': sorted(x for x in p['sector'].dropna().unique() if x),
        'ministries': sorted(x for x in p['ministry'].dropna().unique() if x),
        'states': sorted(x for x in p['state'].dropna().unique() if x)[:80],
    }


def _t_model_info():
    with open(f'{ARTIFACTS_DIR}/model_card.json') as f:
        card = json.load(f)
    tasks = {}
    for name, t in card.get('tasks', {}).items():
        if t.get('available'):
            bm = t.get('best_model') or t.get('model') or 'n/a'
            m = t.get('best_metrics', {})
            tasks[name] = {
                'best_model': bm,
                'metrics': {k: (round(v, 4) if isinstance(v, float) else v)
                            for k, v in m.items()
                            if isinstance(v, (int, float))} if m else None,
            }
        else:
            tasks[name] = {'available': False,
                           'reason': t.get('reason') or t.get('note')}
    shap = card.get('shap_global') or {}
    return _clean({
        'tasks': tasks,
        'top_shap_features': list(zip(
            shap.get('features', [])[:6],
            [round(float(x), 4) for x in shap.get('mean_abs_shap', [])[:6]])),
        'shap_caveat': shap.get('caveat'),
        'split_policy': card.get('split_policy'),
    })


def _t_data_quality():
    panel = query_df('SELECT * FROM panel')
    with open(MANIFEST_JSON) as f:
        manifest = json.load(f)
    return _clean({
        'months': sorted(panel['report_month'].unique()),
        'panel_rows': int(len(panel)),
        'unique_projects': int(panel['project_code'].nunique()),
        'validation': manifest.get('validation'),
        'sources': {k: v['report'] for k, v in
                    manifest.get('sources', {}).items()},
        'data_dir_note': f'manifest at {DATA_DIR}/source_manifest.json',
    })


TOOLS = [
    {'name': 'get_overview',
     'description': 'Latest-month portfolio overview of ongoing MoSPI '
                    'central-sector projects: counts, overrun shares, cost '
                    'totals, risk distribution.',
     'parameters': {'type': 'object', 'properties': {}}},
    {'name': 'get_top_risk_projects',
     'description': 'Top-N highest implementation-risk ongoing projects, '
                    'optionally filtered by sector, ministry or state.',
     'parameters': {'type': 'object', 'properties': {
         'n': {'type': 'integer', 'description': 'how many (default 10, max 25)'},
         'sector': {'type': 'string'},
         'ministry': {'type': 'string'},
         'state': {'type': 'string'}}}},
    {'name': 'find_project',
     'description': 'Full details (costs, overrun, delay, risk score, model '
                    'probability, active warnings) for one project by code '
                    'or name.',
     'parameters': {'type': 'object', 'required': ['query'], 'properties': {
         'query': {'type': 'string',
                   'description': 'project code (e.g. N24001451) or name'}}}},
    {'name': 'get_aggregate',
     'description': 'Aggregate statistics (counts, overrun/delay shares, '
                    'cost totals, top risky) for ongoing projects within one '
                    'sector, ministry or state.',
     'parameters': {'type': 'object', 'properties': {
         'sector': {'type': 'string'},
         'ministry': {'type': 'string'},
         'state': {'type': 'string'}}}},
    {'name': 'get_filter_values',
     'description': 'Valid sector, ministry and state names for filtering.',
     'parameters': {'type': 'object', 'properties': {}}},
    {'name': 'get_model_info',
     'description': 'PAIMANA model card: task winners with metrics, honest '
                    'rejections, top SHAP influences.',
     'parameters': {'type': 'object', 'properties': {}}},
    {'name': 'get_data_quality',
     'description': 'Dataset coverage, source reports and parse-validation '
                    'results.',
     'parameters': {'type': 'object', 'properties': {}}},
]

_IMPLS = {
    'get_overview': _t_overview,
    'get_top_risk_projects': _t_top_risk,
    'find_project': _t_find_project,
    'get_aggregate': _t_aggregate,
    'get_filter_values': _t_filter_values,
    'get_model_info': _t_model_info,
    'get_data_quality': _t_data_quality,
}


# --------------------------------------------------------------------------
# transport (module-level so tests can monkeypatch it)
# --------------------------------------------------------------------------
def _post(url, payload, api_key):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={'Content-Type': 'application/json',
                 'x-goog-api-key': api_key},
        method='POST')
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        return json.loads(resp.read().decode())


def _extract(response):
    """Return (text, function_calls, raw_content) from a generateContent body."""
    cands = response.get('candidates') or []
    if not cands:
        return None, [], None
    content = cands[0].get('content') or {}
    text, calls = [], []
    for part in content.get('parts', []):
        if 'text' in part:
            text.append(part['text'])
        fc = part.get('functionCall')
        if fc:
            calls.append({'name': fc.get('name'),
                          'args': fc.get('args') or {},
                          'id': fc.get('id')})
    return (''.join(text).strip() or None), calls, content


def answer_with_gemini(question: str):
    """Answer using Gemini + tool grounding. Returns a dict, or None on any
    failure (caller falls back to the rule-based engine)."""
    api_key = get_setting('GEMINI_API_KEY')
    if not api_key or not question or not question.strip():
        return None
    if not _rate_ok():
        return None        # too many calls this minute - use the rules engine


    model = get_setting('GEMINI_MODEL') or DEFAULT_MODEL
    contents = [{'role': 'user', 'parts': [{'text': question.strip()}]}]
    payload_base = {
        'systemInstruction': {'parts': [{'text': SYSTEM_PROMPT}]},
        'tools': [{'functionDeclarations': TOOLS}],
        'generationConfig': {'temperature': 0.2, 'maxOutputTokens': 1024},
    }
    try:
        for _ in range(MAX_TOOL_ROUNDS):
            payload = dict(payload_base, contents=contents)
            resp = _post(API_URL.format(model=model), payload, api_key)
            text, calls, content = _extract(resp)
            if not calls:
                if text:
                    return {'answer': text, 'engine': 'gemini', 'intent': 'llm',
                            'model': model}
                return None                      # blocked / empty response
            contents.append({'role': 'model', 'parts': content['parts']})
            parts = []
            for c in calls:
                try:
                    result = _IMPLS[c['name']](**c['args'])
                except Exception as e:                      # noqa: BLE001
                    result = {'error': f'tool failed: {e!r}'}
                fr = {'name': c['name'], 'response':
                      {'result': result if result is not None else {}}}
                if c.get('id'):
                    fr['id'] = c['id']
                parts.append({'functionResponse': fr})
            contents.append({'role': 'user', 'parts': parts})
        return None                                # tool loop did not converge
    except Exception:                              # noqa: BLE001
        return None


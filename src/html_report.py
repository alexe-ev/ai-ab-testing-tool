"""
HTML Report: self-contained interactive dashboard.

Generates a single .html file with all data embedded.
Open in any browser, no server needed.
"""

import json
from pathlib import Path


def generate_html_report(
    analysis_path: str,
    run_path: str,
    eval_path: str,
    output_dir: str = "results",
) -> str:
    with open(analysis_path) as f:
        analysis_data = json.load(f)
    with open(run_path) as f:
        run_data = json.load(f)
    with open(eval_path) as f:
        eval_data = json.load(f)

    a = analysis_data["analysis"]
    name_a = a["prompt_a"]["name"]
    name_b = a["prompt_b"]["name"]

    html = _build_html(analysis_data, run_data, eval_data)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    base_id = analysis_data["analysis_id"].removeprefix("analysis_")
    html_file = output_path / f"report_{base_id}.html"

    with open(html_file, "w") as f:
        f.write(html)

    print(f"✅ HTML report saved to {html_file}")
    return str(html_file)


def _esc(s):
    """Escape for safe HTML embedding."""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _build_html(analysis_data: dict, run_data: dict, eval_data: dict) -> str:
    a = analysis_data["analysis"]
    name_a = a["prompt_a"]["name"]
    name_b = a["prompt_b"]["name"]
    exp_name = _esc(run_data["config"]["experiment"].get("name", "Unnamed"))
    model = _esc(run_data["config"]["model"]["name"])
    total_cases = run_data["summary"]["total_cases"]
    timestamp = analysis_data.get("timestamp", "")

    rec = a.get("recommendation", {})
    winner = rec.get("winner", "inconclusive")
    confidence = rec.get("confidence", "low")

    # Pointwise data
    pw = a.get("pointwise", {})
    dims = pw.get("dimensions", {})
    overall = pw.get("overall_weighted", {})

    # Pairwise data
    pair = a.get("pairwise", {})

    # Category data
    cats = a.get("category_breakdown", {})

    # Notable cases
    notable = a.get("notable_cases", {})

    # Build dimension rows
    dim_rows = ""
    dim_chart_data = []
    for dim_name, dim_data in dims.items():
        ma = dim_data[name_a]["mean"]
        mb = dim_data[name_b]["mean"]
        sa = dim_data[name_a]["std"]
        sb = dim_data[name_b]["std"]
        diff = dim_data["comparison"]["mean_diff"]
        p_val = dim_data["comparison"]["ttest"].get("p_value")
        d_val = dim_data["comparison"].get("cohens_d")
        effect = dim_data["comparison"].get("effect_interpretation", "?")
        better = dim_data["comparison"]["better"]

        p_str = f"{p_val:.3f}" if p_val is not None else "n/a"
        d_str = f"{d_val:.2f}" if d_val is not None else "n/a"

        sig_cls = ""
        sig_badge = ""
        if p_val is not None and p_val < 0.05:
            sig_cls = "sig-005"
            sig_badge = '<span class="badge badge-sig">p&lt;.05</span>'
        elif p_val is not None and p_val < 0.10:
            sig_cls = "sig-010"
            sig_badge = '<span class="badge badge-marginal">p&lt;.10</span>'

        winner_cls_a = "winner-cell" if better == name_a else ""
        winner_cls_b = "winner-cell" if better == name_b else ""

        dim_rows += f"""<tr class="{sig_cls}">
            <td class="dim-name">{_esc(dim_name)}</td>
            <td class="{winner_cls_a}">{ma:.2f} <span class="std">&plusmn;{sa:.2f}</span></td>
            <td class="{winner_cls_b}">{mb:.2f} <span class="std">&plusmn;{sb:.2f}</span></td>
            <td class="delta {'delta-pos' if diff > 0 else 'delta-neg' if diff < 0 else ''}">{diff:+.2f}</td>
            <td>{p_str} {sig_badge}</td>
            <td>{d_str} <span class="effect-label">{effect}</span></td>
        </tr>"""

        dim_chart_data.append({"name": dim_name, "a": ma, "b": mb})

    # Overall row
    overall_row = ""
    if overall:
        oa = overall.get(name_a, 0)
        ob = overall.get(name_b, 0)
        ob_name = overall.get("better", "?")
        winner_cls_a = "winner-cell" if ob_name == name_a else ""
        winner_cls_b = "winner-cell" if ob_name == name_b else ""
        overall_row = f"""<tr class="overall-row">
            <td class="dim-name">Overall (weighted)</td>
            <td class="{winner_cls_a}"><strong>{oa:.2f}</strong></td>
            <td class="{winner_cls_b}"><strong>{ob:.2f}</strong></td>
            <td></td><td></td><td></td>
        </tr>"""

    # Pairwise section
    pairwise_html = ""
    if pair:
        total_pw = pair.get("total", 0)
        wins_a = pair.get(f"wins_{name_a}", 0)
        wins_b = pair.get(f"wins_{name_b}", 0)
        ties = pair.get("ties", 0)
        uncertain = pair.get("uncertain", 0)
        consistency = pair.get("swap_test_consistency")
        wr_a = pair.get(f"win_rate_{name_a}")
        wr_b = pair.get(f"win_rate_{name_b}")

        decided = wins_a + wins_b + ties
        pct_a = (wins_a / decided * 100) if decided > 0 else 0
        pct_b = (wins_b / decided * 100) if decided > 0 else 0
        pct_tie = (ties / decided * 100) if decided > 0 else 0

        consistency_pct = (consistency * 100) if consistency is not None else 0
        consistency_cls = "good" if consistency_pct >= 80 else "warn"

        pairwise_html = f"""
        <div class="section">
            <h2>Head-to-Head Comparison</h2>
            <div class="pairwise-grid">
                <div class="pw-bar-container">
                    <div class="pw-bar">
                        <div class="pw-segment pw-a" style="width:{pct_a:.1f}%">
                            {_esc(name_a)} {wins_a}
                        </div>
                        <div class="pw-segment pw-tie" style="width:{pct_tie:.1f}%">
                            Tie {ties}
                        </div>
                        <div class="pw-segment pw-b" style="width:{pct_b:.1f}%">
                            {_esc(name_b)} {wins_b}
                        </div>
                    </div>
                    {'<div class="pw-uncertain">+ ' + str(uncertain) + ' uncertain (positional bias)</div>' if uncertain > 0 else ''}
                </div>
                <div class="pw-stats">
                    <div class="stat-card">
                        <div class="stat-value">{total_pw}</div>
                        <div class="stat-label">comparisons</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value {consistency_cls}">{consistency_pct:.0f}%</div>
                        <div class="stat-label">swap consistency</div>
                    </div>
                </div>
            </div>
        </div>"""

    # Category breakdown
    category_html = ""
    if cats:
        cat_rows = ""
        for cat, data in sorted(cats.items()):
            ca = data[name_a]
            cb = data[name_b]
            better = data["better"]
            bar_max = 5
            cat_rows += f"""<tr>
                <td>{_esc(cat)}</td>
                <td>{data['n_cases']}</td>
                <td>
                    <div class="mini-bar-wrap">
                        <div class="mini-bar bar-a" style="width:{ca/bar_max*100:.0f}%"></div>
                        <span class="mini-bar-val">{ca:.2f}</span>
                    </div>
                </td>
                <td>
                    <div class="mini-bar-wrap">
                        <div class="mini-bar bar-b" style="width:{cb/bar_max*100:.0f}%"></div>
                        <span class="mini-bar-val">{cb:.2f}</span>
                    </div>
                </td>
                <td class="better-cell">{_esc(better)}</td>
            </tr>"""

        category_html = f"""
        <div class="section">
            <h2>Breakdown by Category</h2>
            <table class="data-table">
                <thead><tr>
                    <th>Category</th><th>N</th>
                    <th>{_esc(name_a)}</th><th>{_esc(name_b)}</th><th>Better</th>
                </tr></thead>
                <tbody>{cat_rows}</tbody>
            </table>
        </div>"""

    # Notable cases
    notable_html = ""
    for label, cases in notable.items():
        if not cases:
            continue
        pretty = label.replace("best_for_", "")
        cards = ""
        for c in cases:
            input_text = c["input"][:200] + "..." if len(c["input"]) > 200 else c["input"]
            delta = c["mean_delta"]
            cards += f"""<div class="notable-card">
                <div class="notable-header">
                    <span class="notable-id">{_esc(c['test_case_id'])}</span>
                    <span class="notable-cat">{_esc(c['category'])}</span>
                    <span class="notable-delta {'delta-pos' if delta > 0 else 'delta-neg'}">&Delta; {delta:+.2f}</span>
                </div>
                <div class="notable-input">{_esc(input_text)}</div>
            </div>"""
        notable_html += f"""
        <div class="notable-group">
            <h3>Best for {_esc(pretty)}</h3>
            {cards}
        </div>"""

    if notable_html:
        notable_html = f'<div class="section"><h2>Notable Cases</h2>{notable_html}</div>'

    # Response viewer: build case data for JS
    cases_json = _build_cases_json(run_data, eval_data, a)

    # Recommendation styling
    if winner == "inconclusive":
        rec_cls = "rec-inconclusive"
        rec_text = "Inconclusive"
        rec_sub = "Data does not clearly favor either prompt."
    else:
        rec_cls = "rec-high" if confidence == "high" else "rec-medium"
        rec_text = f"{_esc(winner)}"
        rec_sub = f"Confidence: {confidence}"

    # Chart bars
    chart_html = ""
    if dim_chart_data:
        bars = ""
        for d in dim_chart_data:
            bars += f"""
            <div class="chart-row">
                <div class="chart-label">{_esc(d['name'])}</div>
                <div class="chart-bars">
                    <div class="chart-bar bar-a" style="width:{d['a']/5*100:.0f}%">
                        <span>{d['a']:.2f}</span>
                    </div>
                    <div class="chart-bar bar-b" style="width:{d['b']/5*100:.0f}%">
                        <span>{d['b']:.2f}</span>
                    </div>
                </div>
            </div>"""
        chart_html = f"""
        <div class="section">
            <h2>Score Comparison</h2>
            <div class="chart-legend">
                <span class="legend-item"><span class="legend-dot dot-a"></span> {_esc(name_a)}</span>
                <span class="legend-item"><span class="legend-dot dot-b"></span> {_esc(name_b)}</span>
            </div>
            <div class="chart-container">{bars}</div>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>A/B Report: {exp_name}</title>
<style>
:root {{
    --bg: #0f1117;
    --surface: #1a1d27;
    --surface2: #232734;
    --border: #2e3348;
    --text: #e1e4ed;
    --text2: #8b90a5;
    --accent-a: #6c9fff;
    --accent-a-bg: rgba(108,159,255,0.12);
    --accent-b: #f0a456;
    --accent-b-bg: rgba(240,164,86,0.12);
    --green: #5cb97a;
    --red: #e5635d;
    --yellow: #e8c34a;
    --radius: 8px;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.5;
    padding: 24px;
    max-width: 1100px;
    margin: 0 auto;
}}
h1 {{ font-size: 1.5rem; font-weight: 600; margin-bottom: 4px; }}
h2 {{ font-size: 1.1rem; font-weight: 600; margin-bottom: 16px; color: var(--text); }}
h3 {{ font-size: 0.95rem; font-weight: 600; margin-bottom: 10px; color: var(--text2); }}

.header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 24px;
    padding-bottom: 20px;
    border-bottom: 1px solid var(--border);
}}
.header-left h1 {{ margin-bottom: 8px; }}
.meta {{ display: flex; gap: 16px; flex-wrap: wrap; }}
.meta-item {{ font-size: 0.8rem; color: var(--text2); }}
.meta-item strong {{ color: var(--text); }}

.rec-card {{
    padding: 16px 24px;
    border-radius: var(--radius);
    text-align: center;
    min-width: 180px;
}}
.rec-high {{ background: rgba(92,185,122,0.12); border: 1px solid rgba(92,185,122,0.3); }}
.rec-medium {{ background: rgba(232,195,74,0.12); border: 1px solid rgba(232,195,74,0.3); }}
.rec-inconclusive {{ background: var(--surface); border: 1px solid var(--border); }}
.rec-label {{ font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text2); margin-bottom: 4px; }}
.rec-winner {{ font-size: 1.3rem; font-weight: 700; }}
.rec-high .rec-winner {{ color: var(--green); }}
.rec-medium .rec-winner {{ color: var(--yellow); }}
.rec-inconclusive .rec-winner {{ color: var(--text2); }}
.rec-conf {{ font-size: 0.75rem; color: var(--text2); margin-top: 2px; }}

.section {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px;
    margin-bottom: 16px;
}}

.data-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
}}
.data-table th {{
    text-align: left;
    padding: 8px 12px;
    border-bottom: 2px solid var(--border);
    color: var(--text2);
    font-weight: 500;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}}
.data-table td {{
    padding: 10px 12px;
    border-bottom: 1px solid var(--border);
}}
.data-table tr:last-child td {{ border-bottom: none; }}
.data-table .overall-row td {{
    border-top: 2px solid var(--border);
    padding-top: 14px;
}}
.dim-name {{ font-weight: 500; }}
.std {{ color: var(--text2); font-size: 0.8em; }}
.delta-pos {{ color: var(--accent-a); }}
.delta-neg {{ color: var(--accent-b); }}
.winner-cell {{ font-weight: 600; }}
.effect-label {{ color: var(--text2); font-size: 0.8em; }}
.badge {{
    font-size: 0.65rem;
    padding: 2px 6px;
    border-radius: 3px;
    font-weight: 600;
    text-transform: uppercase;
}}
.badge-sig {{ background: rgba(92,185,122,0.2); color: var(--green); }}
.badge-marginal {{ background: rgba(232,195,74,0.15); color: var(--yellow); }}

/* Chart */
.chart-container {{ display: flex; flex-direction: column; gap: 12px; }}
.chart-row {{ display: flex; align-items: center; gap: 12px; }}
.chart-label {{ width: 130px; font-size: 0.8rem; color: var(--text2); text-align: right; flex-shrink: 0; }}
.chart-bars {{ flex: 1; display: flex; flex-direction: column; gap: 4px; }}
.chart-bar {{
    height: 22px;
    border-radius: 3px;
    display: flex;
    align-items: center;
    padding-left: 8px;
    font-size: 0.75rem;
    font-weight: 600;
    min-width: 40px;
    transition: width 0.5s ease;
}}
.bar-a {{ background: var(--accent-a-bg); color: var(--accent-a); border: 1px solid rgba(108,159,255,0.25); }}
.bar-b {{ background: var(--accent-b-bg); color: var(--accent-b); border: 1px solid rgba(240,164,86,0.25); }}
.chart-legend {{ display: flex; gap: 20px; margin-bottom: 14px; }}
.legend-item {{ font-size: 0.8rem; color: var(--text2); display: flex; align-items: center; gap: 6px; }}
.legend-dot {{ width: 10px; height: 10px; border-radius: 2px; }}
.dot-a {{ background: var(--accent-a); }}
.dot-b {{ background: var(--accent-b); }}

/* Pairwise */
.pairwise-grid {{ display: flex; flex-direction: column; gap: 16px; }}
.pw-bar-container {{ width: 100%; }}
.pw-bar {{
    display: flex;
    height: 40px;
    border-radius: 6px;
    overflow: hidden;
    font-size: 0.8rem;
    font-weight: 600;
}}
.pw-segment {{
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 40px;
    transition: width 0.5s ease;
}}
.pw-a {{ background: var(--accent-a-bg); color: var(--accent-a); }}
.pw-b {{ background: var(--accent-b-bg); color: var(--accent-b); }}
.pw-tie {{ background: var(--surface2); color: var(--text2); }}
.pw-uncertain {{ font-size: 0.75rem; color: var(--text2); margin-top: 6px; }}
.pw-stats {{ display: flex; gap: 12px; }}
.stat-card {{
    background: var(--surface2);
    border-radius: var(--radius);
    padding: 12px 20px;
    text-align: center;
}}
.stat-value {{ font-size: 1.3rem; font-weight: 700; }}
.stat-value.good {{ color: var(--green); }}
.stat-value.warn {{ color: var(--yellow); }}
.stat-label {{ font-size: 0.7rem; color: var(--text2); text-transform: uppercase; letter-spacing: 0.04em; }}

/* Mini bars for category */
.mini-bar-wrap {{
    display: flex;
    align-items: center;
    gap: 8px;
}}
.mini-bar {{
    height: 8px;
    border-radius: 4px;
    min-width: 4px;
}}
.mini-bar-val {{ font-size: 0.8rem; font-weight: 500; color: var(--text2); }}
.better-cell {{ font-weight: 600; font-size: 0.85rem; }}

/* Notable */
.notable-group {{ margin-bottom: 16px; }}
.notable-card {{
    background: var(--surface2);
    border-radius: 6px;
    padding: 12px;
    margin-bottom: 8px;
}}
.notable-header {{ display: flex; gap: 10px; align-items: center; margin-bottom: 6px; }}
.notable-id {{ font-weight: 600; font-size: 0.85rem; }}
.notable-cat {{ font-size: 0.7rem; color: var(--text2); background: var(--surface); padding: 2px 8px; border-radius: 3px; }}
.notable-delta {{ font-size: 0.8rem; font-weight: 600; margin-left: auto; }}
.notable-input {{ font-size: 0.8rem; color: var(--text2); line-height: 1.4; }}

/* Tabs */
.tabs {{
    display: flex;
    gap: 2px;
    margin-bottom: 16px;
    background: var(--surface2);
    border-radius: 6px;
    padding: 3px;
    width: fit-content;
}}
.tab {{
    padding: 6px 16px;
    font-size: 0.8rem;
    border: none;
    background: none;
    color: var(--text2);
    cursor: pointer;
    border-radius: 4px;
    font-weight: 500;
    transition: all 0.15s;
}}
.tab:hover {{ color: var(--text); }}
.tab.active {{ background: var(--surface); color: var(--text); }}
.tab-panel {{ display: none; }}
.tab-panel.active {{ display: block; }}

/* Response viewer */
.viewer-controls {{
    display: flex;
    gap: 10px;
    align-items: center;
    margin-bottom: 16px;
    flex-wrap: wrap;
}}
.viewer-select {{
    background: var(--surface2);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 0.85rem;
}}
.viewer-nav {{
    display: flex;
    gap: 4px;
}}
.viewer-nav button {{
    background: var(--surface2);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 4px 12px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.85rem;
}}
.viewer-nav button:hover {{ background: var(--border); }}
.viewer-case-label {{
    font-size: 0.8rem;
    color: var(--text2);
    margin-left: auto;
}}
.response-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}}
.response-col {{
    background: var(--surface2);
    border-radius: 6px;
    padding: 14px;
}}
.response-col h4 {{
    font-size: 0.8rem;
    margin-bottom: 10px;
    padding-bottom: 6px;
    border-bottom: 1px solid var(--border);
}}
.response-col h4.col-a {{ color: var(--accent-a); }}
.response-col h4.col-b {{ color: var(--accent-b); }}
.response-text {{
    font-size: 0.8rem;
    color: var(--text);
    line-height: 1.6;
    white-space: pre-wrap;
    max-height: 400px;
    overflow-y: auto;
}}
.response-meta {{
    font-size: 0.7rem;
    color: var(--text2);
    margin-top: 10px;
    padding-top: 8px;
    border-top: 1px solid var(--border);
    display: flex;
    gap: 12px;
}}
.user-input {{
    background: var(--surface2);
    border-radius: 6px;
    padding: 12px;
    margin-bottom: 12px;
    font-size: 0.85rem;
    color: var(--text2);
    border-left: 3px solid var(--border);
}}
.user-input strong {{ color: var(--text); }}
.scores-inline {{
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    margin-top: 8px;
}}
.score-chip {{
    font-size: 0.7rem;
    padding: 2px 8px;
    border-radius: 3px;
    font-weight: 500;
}}
.score-chip-a {{ background: var(--accent-a-bg); color: var(--accent-a); }}
.score-chip-b {{ background: var(--accent-b-bg); color: var(--accent-b); }}

.footer {{
    text-align: center;
    padding: 20px;
    font-size: 0.75rem;
    color: var(--text2);
}}
</style>
</head>
<body>

<div class="header">
    <div class="header-left">
        <h1>{exp_name}</h1>
        <div class="meta">
            <span class="meta-item"><strong>Model:</strong> {model}</span>
            <span class="meta-item"><strong>Cases:</strong> {total_cases}</span>
            <span class="meta-item"><strong>Prompts:</strong> {_esc(name_a)} vs {_esc(name_b)}</span>
        </div>
    </div>
    <div class="rec-card {rec_cls}">
        <div class="rec-label">Recommendation</div>
        <div class="rec-winner">{rec_text}</div>
        <div class="rec-conf">{rec_sub}</div>
    </div>
</div>

<div class="tabs" id="mainTabs">
    <button class="tab active" data-tab="overview">Overview</button>
    <button class="tab" data-tab="responses">Responses</button>
</div>

<div class="tab-panel active" id="tab-overview">

{chart_html}

<div class="section">
    <h2>Scores by Dimension</h2>
    <table class="data-table">
        <thead><tr>
            <th>Dimension</th>
            <th>{_esc(name_a)}</th>
            <th>{_esc(name_b)}</th>
            <th>&Delta;</th>
            <th>p-value</th>
            <th>Effect size</th>
        </tr></thead>
        <tbody>
            {dim_rows}
            {overall_row}
        </tbody>
    </table>
</div>

{pairwise_html}
{category_html}
{notable_html}

</div>

<div class="tab-panel" id="tab-responses">
    <div class="section">
        <h2>Response Viewer</h2>
        <div class="viewer-controls">
            <select class="viewer-select" id="caseFilter">
                <option value="all">All categories</option>
            </select>
            <div class="viewer-nav">
                <button onclick="prevCase()">&larr; Prev</button>
                <button onclick="nextCase()">Next &rarr;</button>
            </div>
            <span class="viewer-case-label" id="caseLabel">1 / {total_cases}</span>
        </div>
        <div id="responseViewer"></div>
    </div>
</div>

<div class="footer">
    Generated by <strong>prompt-ab</strong>
</div>

<script>
const CASES = {cases_json};
const NAME_A = {json.dumps(name_a)};
const NAME_B = {json.dumps(name_b)};
const KEY_A = {json.dumps(a["prompt_a"]["key"])};
const KEY_B = {json.dumps(a["prompt_b"]["key"])};

// Tabs
document.querySelectorAll('.tab').forEach(tab => {{
    tab.addEventListener('click', () => {{
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById('tab-' + tab.dataset.tab).classList.add('active');
    }});
}});

// Response viewer
let currentIdx = 0;
let filteredCases = [...CASES];

function populateFilter() {{
    const cats = [...new Set(CASES.map(c => c.category))].sort();
    const sel = document.getElementById('caseFilter');
    cats.forEach(cat => {{
        const opt = document.createElement('option');
        opt.value = cat;
        opt.textContent = cat;
        sel.appendChild(opt);
    }});
    sel.addEventListener('change', () => {{
        const v = sel.value;
        filteredCases = v === 'all' ? [...CASES] : CASES.filter(c => c.category === v);
        currentIdx = 0;
        renderCase();
    }});
}}

function renderCase() {{
    if (filteredCases.length === 0) {{
        document.getElementById('responseViewer').innerHTML = '<p style="color:var(--text2)">No cases found.</p>';
        document.getElementById('caseLabel').textContent = '0 / 0';
        return;
    }}
    const c = filteredCases[currentIdx];
    document.getElementById('caseLabel').textContent =
        (currentIdx + 1) + ' / ' + filteredCases.length + '  [' + c.id + ']';

    const respA = c.responses[KEY_A] || {{}};
    const respB = c.responses[KEY_B] || {{}};

    function scoreChips(scores, cls) {{
        if (!scores) return '';
        return '<div class="scores-inline">' +
            Object.entries(scores).map(([dim, data]) =>
                '<span class="score-chip ' + cls + '">' + dim + ': ' + (data.score || '?') + '</span>'
            ).join('') + '</div>';
    }}

    const html = `
        <div class="user-input"><strong>Customer:</strong> ${{esc(c.input)}}</div>
        <div class="response-grid">
            <div class="response-col">
                <h4 class="col-a">${{NAME_A}}</h4>
                <div class="response-text">${{esc(respA.response || 'No response')}}</div>
                ${{scoreChips(c.scores_a, 'score-chip-a')}}
                <div class="response-meta">
                    <span>${{respA.input_tokens || '?'}} + ${{respA.output_tokens || '?'}} tokens</span>
                    <span>${{respA.latency_seconds || '?'}}s</span>
                </div>
            </div>
            <div class="response-col">
                <h4 class="col-b">${{NAME_B}}</h4>
                <div class="response-text">${{esc(respB.response || 'No response')}}</div>
                ${{scoreChips(c.scores_b, 'score-chip-b')}}
                <div class="response-meta">
                    <span>${{respB.input_tokens || '?'}} + ${{respB.output_tokens || '?'}} tokens</span>
                    <span>${{respB.latency_seconds || '?'}}s</span>
                </div>
            </div>
        </div>`;
    document.getElementById('responseViewer').innerHTML = html;
}}

function nextCase() {{ currentIdx = (currentIdx + 1) % filteredCases.length; renderCase(); }}
function prevCase() {{ currentIdx = (currentIdx - 1 + filteredCases.length) % filteredCases.length; renderCase(); }}

function esc(s) {{
    const d = document.createElement('div');
    d.textContent = s || '';
    return d.innerHTML;
}}

populateFilter();
renderCase();

// Keyboard navigation
document.addEventListener('keydown', (e) => {{
    if (e.key === 'ArrowRight') nextCase();
    if (e.key === 'ArrowLeft') prevCase();
}});
</script>
</body>
</html>"""


def _build_cases_json(run_data: dict, eval_data: dict, analysis: dict) -> str:
    """Build JSON array of cases with responses and scores for the viewer."""
    key_a = analysis["prompt_a"]["key"]
    key_b = analysis["prompt_b"]["key"]

    evals_by_id = {}
    for e in eval_data.get("evaluations", []):
        evals_by_id[e["test_case_id"]] = e

    cases = []
    for r in run_data["results"]:
        case = {
            "id": r["test_case_id"],
            "category": r.get("category", "unknown"),
            "input": r["input"],
            "responses": r["responses"],
        }

        ev = evals_by_id.get(r["test_case_id"], {})
        pw = ev.get("pointwise", {})
        case["scores_a"] = pw.get(key_a)
        case["scores_b"] = pw.get(key_b)

        cases.append(case)

    return json.dumps(cases, ensure_ascii=False)

from statistics import mean

from .models import EvaluationResult

PASSING_SCORE = 7
MAX_SCORE = 10


def _score_class(score: int) -> str:
    if score >= 9:
        return "s-excellent"
    if score >= PASSING_SCORE:
        return "s-good"
    if score >= 5:
        return "s-medium"
    if score >= 3:
        return "s-poor"
    return "s-bad"


def generate_prompt_evaluation_report(
    evaluation_results: list[EvaluationResult],
) -> str:
    """Render evaluation results as a self-contained HTML report. Scores ≥ `PASSING_SCORE` are highlighted green; lower scores are red."""
    total_tests = len(evaluation_results)
    scores = [result.score for result in evaluation_results]
    average_score = mean(scores) if scores else 0
    pass_rate = (
        100 * sum(1 for score in scores if score >= PASSING_SCORE) / total_tests
        if total_tests
        else 0
    )

    rows = ""
    for result in evaluation_results:
        score_class = _score_class(result.score)
        inputs_html = "".join(
            f'<div class="input-pair">'
            f'<span class="input-key">{key}</span>'
            f'<span class="input-value">{value}</span>'
            f"</div>"
            for key, value in result.test_case.prompt_inputs.items()
        )
        criteria_html = "".join(
            f"<li>{criterion}</li>"
            for criterion in result.test_case.solution_criteria
        )
        rows += f"""
                    <tr class="{score_class}">
                        <td class="scenario">{result.test_case.scenario}</td>
                        <td>{inputs_html}</td>
                        <td><ul class="criteria-list">{criteria_html}</ul></td>
                        <td><pre class="output-block">{result.output}</pre></td>
                        <td class="score-col"><div class="score-badge {score_class}">{result.score}</div></td>
                        <td class="reasoning">{result.reasoning}</td>
                    </tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Prompt Evaluation Report</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}

        body {{
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            background: #f1f5f9;
            color: #0f172a;
            min-height: 100vh;
        }}

        .header {{
            background: #0f172a;
            padding: 36px 48px;
        }}
        .header-inner {{
            max-width: 1600px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            flex-wrap: wrap;
            gap: 32px;
        }}
        .header h1 {{
            font-size: 22px;
            font-weight: 700;
            color: #f8fafc;
            letter-spacing: -0.01em;
        }}
        .header-subtitle {{
            font-size: 13px;
            color: #64748b;
            margin-top: 4px;
        }}

        .stats {{
            display: flex;
            gap: 40px;
        }}
        .stat-label {{
            font-size: 11px;
            font-weight: 600;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }}
        .stat-value {{
            font-size: 32px;
            font-weight: 700;
            color: #f8fafc;
            line-height: 1.1;
            margin-top: 6px;
        }}
        .stat-unit {{
            font-size: 16px;
            font-weight: 400;
            color: #64748b;
        }}

        .main {{
            max-width: 1600px;
            margin: 32px auto;
            padding: 0 48px 48px;
        }}

        .table-wrap {{
            background: #fff;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,.08), 0 1px 2px rgba(0,0,0,.04);
            overflow: hidden;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}

        thead th {{
            background: #f8fafc;
            color: #64748b;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
            white-space: nowrap;
        }}

        tbody tr {{ transition: background 0.1s; }}
        tbody tr:hover td {{ background: #f8fafc; }}
        tbody tr:last-child td {{ border-bottom: none; }}

        td {{
            padding: 16px;
            border-bottom: 1px solid #f1f5f9;
            vertical-align: top;
            color: #334155;
            line-height: 1.55;
        }}

        tr.s-excellent td:first-child {{ border-left: 3px solid #16a34a; }}
        tr.s-good      td:first-child {{ border-left: 3px solid #65a30d; }}
        tr.s-medium    td:first-child {{ border-left: 3px solid #d97706; }}
        tr.s-poor      td:first-child {{ border-left: 3px solid #ea580c; }}
        tr.s-bad       td:first-child {{ border-left: 3px solid #dc2626; }}

        th:nth-child(1), td:nth-child(1) {{ width: 14%; }}
        th:nth-child(2), td:nth-child(2) {{ width: 13%; }}
        th:nth-child(3), td:nth-child(3) {{ width: 14%; }}
        th:nth-child(4), td:nth-child(4) {{ width: 27%; }}
        th:nth-child(5), td:nth-child(5) {{ width: 72px; text-align: center; }}
        th:nth-child(6), td:nth-child(6) {{ width: auto; }}

        .input-pair {{
            display: flex;
            gap: 6px;
            margin-bottom: 5px;
            align-items: baseline;
        }}
        .input-pair:last-child {{ margin-bottom: 0; }}
        .input-key {{
            font-weight: 600;
            color: #6366f1;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            flex-shrink: 0;
        }}
        .input-value {{ color: #475569; }}

        .criteria-list {{
            padding-left: 14px;
            color: #475569;
        }}
        .criteria-list li {{ margin-bottom: 4px; }}
        .criteria-list li:last-child {{ margin-bottom: 0; }}

        .output-block {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 12px;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 12px;
            line-height: 1.6;
            color: #334155;
            white-space: pre-wrap;
            word-wrap: break-word;
            max-height: 280px;
            overflow-y: auto;
            margin: 0;
        }}

        .score-col {{ text-align: center; }}
        .score-badge {{
            width: 42px;
            height: 42px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 15px;
        }}
        .s-excellent {{ background: #dcfce7; color: #15803d; }}
        .s-good      {{ background: #d1fae5; color: #065f46; }}
        .s-medium    {{ background: #fef3c7; color: #92400e; }}
        .s-poor      {{ background: #ffedd5; color: #9a3412; }}
        .s-bad       {{ background: #fee2e2; color: #991b1b; }}

        .reasoning {{
            font-style: italic;
            color: #64748b;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="header-inner">
            <div>
                <h1>Prompt Evaluation Report</h1>
                <p class="header-subtitle">{total_tests} test cases &middot; pass threshold &ge; {PASSING_SCORE}</p>
            </div>
            <div class="stats">
                <div>
                    <div class="stat-label">Total Cases</div>
                    <div class="stat-value">{total_tests}</div>
                </div>
                <div>
                    <div class="stat-label">Avg Score</div>
                    <div class="stat-value">{average_score:.1f}<span class="stat-unit"> / {MAX_SCORE}</span></div>
                </div>
                <div>
                    <div class="stat-label">Pass Rate</div>
                    <div class="stat-value">{pass_rate:.1f}<span class="stat-unit">%</span></div>
                </div>
            </div>
        </div>
    </div>

    <main class="main">
        <div class="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th>Scenario</th>
                        <th>Inputs</th>
                        <th>Criteria</th>
                        <th>Output</th>
                        <th>Score</th>
                        <th>Reasoning</th>
                    </tr>
                </thead>
                <tbody>{rows}
                </tbody>
            </table>
        </div>
    </main>
</body>
</html>"""

from html import escape
from datetime import datetime


def _table(rows):
    if not rows:
        return "<p>No data.</p>"

    headers = list(rows[0].keys())
    out = ["<table border='1' cellspacing='0' cellpadding='5'>"]
    out.append("<tr>" + "".join(f"<th>{escape(str(h))}</th>" for h in headers) + "</tr>")

    for row in rows:
        out.append(
            "<tr>"
            + "".join(
                f"<td>{escape(f'{row.get(h, ''):.6g}' if isinstance(row.get(h), float) else str(row.get(h, '')))}</td>"
                for h in headers
            )
            + "</tr>"
        )

    out.append("</table>")
    return "\n".join(out)


def build_html_report(project, result=None):
    node_rows = [n.model_dump() if hasattr(n, "model_dump") else n.dict() for n in project.nodes]
    member_rows = [m.model_dump() if hasattr(m, "model_dump") else m.dict() for m in project.members]
    support_rows = [s.model_dump() if hasattr(s, "model_dump") else s.dict() for s in project.supports]

    warnings = [] if result is None else result.warnings
    solved = False if result is None else result.solved

    html = f"""
<!doctype html>
<html>
<head>
<meta charset='utf-8'>
<title>{escape(project.project_name)} Report</title>
<style>
body {{ font-family: Arial, sans-serif; line-height: 1.45; max-width: 1100px; margin: 28px auto; }}
h1, h2 {{ color: #17365D; }}
table {{ border-collapse: collapse; margin-bottom: 18px; font-size: 13px; }}
th {{ background: #D9EAF7; }}
.warning {{ background: #fff3f3; border-left: 4px solid #9E2A2B; padding: 8px; margin: 8px 0; }}
.ok {{ background: #f1fff2; border-left: 4px solid #4F7F5F; padding: 8px; }}
</style>
</head>
<body>
<h1>Articulated Structures Studio Report</h1>
<p><strong>Project:</strong> {escape(project.project_name)}</p>
<p><strong>Structure type:</strong> {escape(project.structure_type)}</p>
<p><strong>Unit system:</strong> {escape(project.unit_system)}</p>
<p><strong>Generated:</strong> {datetime.now().isoformat(timespec='seconds')}</p>

<h2>Model Summary</h2>
<p>Nodes: {len(project.nodes)} | Members: {len(project.members)} | Supports: {len(project.supports)} | Load cases: {len(project.load_cases)}</p>

<h2>Nodes</h2>
{_table(node_rows)}

<h2>Members</h2>
{_table(member_rows)}

<h2>Supports</h2>
{_table(support_rows)}

<h2>Solver Status</h2>
<div class='{"ok" if solved else "warning"}'>{'Solved successfully.' if solved else 'Not solved or no result available.'}</div>
"""

    if result is not None and result.solved:
        html += f"""
<h2>Reactions</h2>
{_table(result.reactions)}

<h2>Displacements</h2>
{_table(result.displacements)}

<h2>Member End Forces</h2>
{_table(result.member_forces)}
"""

    html += "<h2>Warnings</h2>"

    if warnings:
        for warning in warnings:
            html += f"<div class='warning'>{escape(warning)}</div>"
    else:
        html += "<div class='ok'>No warnings reported.</div>"

    html += """
<h2>Technical Note</h2>
<p>This is an educational / preliminary structural modelling prototype, not a certified structural design package.</p>
</body>
</html>
"""
    return html
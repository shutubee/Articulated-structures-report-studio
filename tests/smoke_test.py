import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.project_io import new_project
from solver.frame_solver import solve_2d_frame
from reports.report_builder import build_html_report


project = new_project()
result = solve_2d_frame(project)

print("Solved:", result.solved)
print("Warnings:", result.warnings)

print("Reactions:")
for row in result.reactions:
    print(row)

print("Displacements:")
for row in result.displacements:
    print(row)

html = build_html_report(project, result)

print("Report length:", len(html))

assert result.solved, result.warnings
assert len(result.reactions) == 2
assert len(result.member_forces) == 3
assert "Articulated Structures Studio Report" in html
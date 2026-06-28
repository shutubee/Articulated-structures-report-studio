import json
from pathlib import Path
from core.models import Project, Node, Member, Material, Section, Support, LoadCase, Load


def dump_model(model):
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def new_project() -> Project:
    return Project(
        project_name="Pinned Portal Frame Demo",
        nodes=[
            Node(node_id="N1", x=0.0, y=0.0),
            Node(node_id="N2", x=0.0, y=4.0),
            Node(node_id="N3", x=6.0, y=4.0),
            Node(node_id="N4", x=6.0, y=0.0),
        ],
        members=[
            Member(member_id="M1", start_node="N1", end_node="N2", member_type="column"),
            Member(member_id="M2", start_node="N2", end_node="N3", member_type="beam"),
            Member(member_id="M3", start_node="N3", end_node="N4", member_type="column"),
        ],
        materials=[
            Material(material_id="MAT1", name="Steel", E=200000000.0, density=78.5)
        ],
        sections=[
            Section(section_id="SEC1", name="Generic Section", area=0.01, Ixx=0.00008)
        ],
        supports=[
            Support(
                support_id="S1",
                node_id="N1",
                support_type="pinned",
                ux="fixed",
                uy="fixed",
                rz="free",
            ),
            Support(
                support_id="S2",
                node_id="N4",
                support_type="pinned",
                ux="fixed",
                uy="fixed",
                rz="free",
            ),
        ],
        load_cases=[
            LoadCase(
                load_case_id="LC1",
                name="Default Nodal Load",
                loads=[
                    Load(
                        load_id="L1",
                        load_type="nodal_force",
                        target_type="node",
                        target_id="N2",
                        direction="global_y",
                        magnitude=-10.0,
                    )
                ],
            )
        ],
    )


def save_project(project: Project, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(dump_model(project), f, indent=2)


def load_project(path: str | Path) -> Project:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Project(**data)
import matplotlib.pyplot as plt


def plot_geometry(project, result=None, deformation_scale=1.0):
    fig, ax = plt.subplots(figsize=(8, 5.5))
    node_lookup = {node.node_id: node for node in project.nodes}

    for member in project.members:
        n1 = node_lookup.get(member.start_node)
        n2 = node_lookup.get(member.end_node)
        if n1 is None or n2 is None:
            continue
        ax.plot([n1.x, n2.x], [n1.y, n2.y], linewidth=2)
        ax.text((n1.x + n2.x) / 2, (n1.y + n2.y) / 2, f" {member.member_id}")

    for node in project.nodes:
        ax.scatter(node.x, node.y, s=35)
        ax.text(node.x, node.y, f" {node.node_id}", va="bottom")

    for support in project.supports:
        node = node_lookup.get(support.node_id)
        if node is None:
            continue
        ax.text(node.x, node.y - 0.25, support.support_type, ha="center", va="top", fontsize=8)

    if result is not None and getattr(result, "solved", False):
        disp = {row["node_id"]: row for row in result.displacements}
        xs, ys = [], []
        for member in project.members:
            n1 = node_lookup.get(member.start_node)
            n2 = node_lookup.get(member.end_node)
            d1 = disp.get(member.start_node, {})
            d2 = disp.get(member.end_node, {})
            if not n1 or not n2 or not d1 or not d2:
                continue
            x1 = n1.x + deformation_scale * d1.get("ux", 0.0)
            y1 = n1.y + deformation_scale * d1.get("uy", 0.0)
            x2 = n2.x + deformation_scale * d2.get("ux", 0.0)
            y2 = n2.y + deformation_scale * d2.get("uy", 0.0)
            ax.plot([x1, x2], [y1, y2], linestyle="--", linewidth=1)
            xs.extend([x1, x2])
            ys.extend([y1, y2])

    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.grid(True)
    ax.set_title(project.project_name)
    fig.tight_layout()
    return fig
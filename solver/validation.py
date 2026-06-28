import math


def validate_project(project):
    warnings = []

    if not project.nodes:
        warnings.append("No nodes have been defined.")
    if not project.members:
        warnings.append("No members have been defined.")

    node_ids = {node.node_id for node in project.nodes}
    coords = {}

    for node in project.nodes:
        key = (round(node.x, 9), round(node.y, 9), round(node.z, 9))
        if key in coords:
            warnings.append(f"Node {node.node_id} duplicates coordinates of {coords[key]}.")
        coords[key] = node.node_id

    connected = set()

    for member in project.members:
        if member.start_node not in node_ids:
            warnings.append(f"Member {member.member_id} start node does not exist.")
        if member.end_node not in node_ids:
            warnings.append(f"Member {member.member_id} end node does not exist.")
        if member.start_node == member.end_node:
            warnings.append(f"Member {member.member_id} has zero length.")

        if member.start_node in node_ids and member.end_node in node_ids:
            connected.add(member.start_node)
            connected.add(member.end_node)
            n1 = next(n for n in project.nodes if n.node_id == member.start_node)
            n2 = next(n for n in project.nodes if n.node_id == member.end_node)
            if math.isclose((n2.x - n1.x) ** 2 + (n2.y - n1.y) ** 2, 0.0):
                warnings.append(f"Member {member.member_id} has zero geometric length.")

        if member.release_i.moment and member.release_j.moment:
            warnings.append(
                f"Member {member.member_id} has moment releases at both ends. Check axial-only or mechanism behaviour."
            )

    for node_id in sorted(node_ids - connected):
        warnings.append(f"Node {node_id} is not connected to any member.")

    if not project.supports:
        warnings.append("No supports have been assigned.")

    restrained_count = 0

    for support in project.supports:
        if support.node_id not in node_ids:
            warnings.append(f"Support {support.support_id} refers to missing node {support.node_id}.")
        for dof in ("ux", "uy", "rz"):
            if getattr(support, dof) == "fixed":
                restrained_count += 1

    if restrained_count < 3:
        warnings.append(
            "The 2D model has fewer than three restrained degrees of freedom. Rigid body motion or instability is likely."
        )

    return warnings
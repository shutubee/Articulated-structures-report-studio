def build_dof_map(project):
    """Assign ux, uy, rz to each 2D node."""
    dof_map = {}
    counter = 0
    for node in project.nodes:
        dof_map[(node.node_id, "ux")] = counter
        counter += 1
        dof_map[(node.node_id, "uy")] = counter
        counter += 1
        dof_map[(node.node_id, "rz")] = counter
        counter += 1
    return dof_map


def get_restrained_dofs(project, dof_map):
    restrained = []
    for support in project.supports:
        for dof_name in ("ux", "uy", "rz"):
            if getattr(support, dof_name) == "fixed":
                restrained.append(dof_map[(support.node_id, dof_name)])
    return sorted(set(restrained))


def get_free_dofs(total_dofs, restrained_dofs):
    restrained_set = set(restrained_dofs)
    return [i for i in range(total_dofs) if i not in restrained_set]
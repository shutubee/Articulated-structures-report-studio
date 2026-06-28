import math
import numpy as np
from core.models import AnalysisResult
from solver.dof import build_dof_map, get_restrained_dofs, get_free_dofs
from solver.stiffness import frame_element_stiffness_2d, transform_to_global, transformation_matrix_2d
from solver.releases import apply_basic_moment_releases
from solver.validation import validate_project


def _is_critical(warning: str) -> bool:
    critical_phrases = [
        "No nodes",
        "No members",
        "fewer than three restrained",
        "does not exist",
        "zero length",
        "zero geometric length",
    ]
    return any(phrase in warning for phrase in critical_phrases)


def solve_2d_frame(project):
    warnings = validate_project(project)
    if any(_is_critical(w) for w in warnings):
        return AnalysisResult(solved=False, warnings=warnings)

    node_lookup = {node.node_id: node for node in project.nodes}
    material_lookup = {mat.material_id: mat for mat in project.materials}
    section_lookup = {sec.section_id: sec for sec in project.sections}
    dof_map = build_dof_map(project)
    total_dofs = len(dof_map)

    K = np.zeros((total_dofs, total_dofs), dtype=float)
    F = np.zeros(total_dofs, dtype=float)

    for member in project.members:
        ni = node_lookup[member.start_node]
        nj = node_lookup[member.end_node]

        dx = nj.x - ni.x
        dy = nj.y - ni.y
        L = math.sqrt(dx**2 + dy**2)
        c = dx / L
        s = dy / L

        mat = material_lookup.get(member.material_id)
        sec = section_lookup.get(member.section_id)

        if mat is None:
            warnings.append(f"Member {member.member_id} references missing material {member.material_id}.")
            continue
        if sec is None:
            warnings.append(f"Member {member.member_id} references missing section {member.section_id}.")
            continue

        k_local = frame_element_stiffness_2d(mat.E, sec.area, sec.Ixx, L)
        k_local = apply_basic_moment_releases(
            k_local,
            release_i=member.release_i.moment,
            release_j=member.release_j.moment,
        )
        k_global = transform_to_global(k_local, c, s)

        member_dofs = [
            dof_map[(member.start_node, "ux")],
            dof_map[(member.start_node, "uy")],
            dof_map[(member.start_node, "rz")],
            dof_map[(member.end_node, "ux")],
            dof_map[(member.end_node, "uy")],
            dof_map[(member.end_node, "rz")],
        ]

        for a in range(6):
            for b in range(6):
                K[member_dofs[a], member_dofs[b]] += k_global[a, b]

    active_load_case = project.load_cases[0] if project.load_cases else None

    if active_load_case:
        for load in active_load_case.loads:
            if load.target_type == "node":
                if load.target_id not in node_lookup:
                    warnings.append(f"Load {load.load_id} targets missing node {load.target_id}.")
                    continue

                if load.direction == "global_x":
                    F[dof_map[(load.target_id, "ux")]] += load.magnitude
                elif load.direction == "global_y":
                    F[dof_map[(load.target_id, "uy")]] += load.magnitude
                elif load.direction == "moment_z":
                    F[dof_map[(load.target_id, "rz")]] += load.magnitude
                else:
                    warnings.append(f"Load {load.load_id} has unsupported direction {load.direction}.")
            else:
                warnings.append(f"Load {load.load_id} uses unsupported target type {load.target_type} in MVP.")

    restrained = get_restrained_dofs(project, dof_map)
    free = get_free_dofs(total_dofs, restrained)

    if not free:
        warnings.append("All degrees of freedom are restrained; no unknown displacement remains.")
        return AnalysisResult(solved=False, warnings=warnings)

    Kff = K[np.ix_(free, free)]
    Ff = F[free]

    try:
        condition_number = np.linalg.cond(Kff)
        if condition_number > 1e12:
            warnings.append(
                f"The stiffness matrix is poorly conditioned (cond={condition_number:.2e}). The model may be close to a mechanism."
            )
        uf = np.linalg.solve(Kff, Ff)

    except np.linalg.LinAlgError:
        warnings.append("The stiffness matrix is singular. The model is unstable or under-constrained.")
        return AnalysisResult(solved=False, warnings=warnings)

    u = np.zeros(total_dofs, dtype=float)

    for idx, dof in enumerate(free):
        u[dof] = uf[idx]

    R = K @ u - F

    displacement_rows = [
        {
            "node_id": node.node_id,
            "ux": u[dof_map[(node.node_id, "ux")]],
            "uy": u[dof_map[(node.node_id, "uy")]],
            "rz": u[dof_map[(node.node_id, "rz")]],
        }
        for node in project.nodes
    ]

    reaction_rows = []

    for support in project.supports:
        reaction_rows.append(
            {
                "support_id": support.support_id,
                "node_id": support.node_id,
                "Rx": R[dof_map[(support.node_id, "ux")]],
                "Ry": R[dof_map[(support.node_id, "uy")]],
                "Mz": R[dof_map[(support.node_id, "rz")]],
            }
        )

    member_force_rows = recover_member_end_forces(
        project, node_lookup, material_lookup, section_lookup, dof_map, u
    )

    return AnalysisResult(
        solved=True,
        warnings=warnings,
        reactions=reaction_rows,
        member_forces=member_force_rows,
        displacements=displacement_rows,
    )


def recover_member_end_forces(project, node_lookup, material_lookup, section_lookup, dof_map, displacements):
    rows = []

    for member in project.members:
        ni = node_lookup[member.start_node]
        nj = node_lookup[member.end_node]

        dx = nj.x - ni.x
        dy = nj.y - ni.y
        L = math.sqrt(dx**2 + dy**2)
        c = dx / L
        s = dy / L

        mat = material_lookup[member.material_id]
        sec = section_lookup[member.section_id]

        k_local = frame_element_stiffness_2d(mat.E, sec.area, sec.Ixx, L)
        k_local = apply_basic_moment_releases(
            k_local,
            release_i=member.release_i.moment,
            release_j=member.release_j.moment,
        )

        T = transformation_matrix_2d(c, s)

        member_dofs = [
            dof_map[(member.start_node, "ux")],
            dof_map[(member.start_node, "uy")],
            dof_map[(member.start_node, "rz")],
            dof_map[(member.end_node, "ux")],
            dof_map[(member.end_node, "uy")],
            dof_map[(member.end_node, "rz")],
        ]

        u_local = T @ displacements[member_dofs]
        f_local = k_local @ u_local

        rows.append(
            {
                "member_id": member.member_id,
                "N_i": f_local[0],
                "V_i": f_local[1],
                "M_i": f_local[2],
                "N_j": f_local[3],
                "V_j": f_local[4],
                "M_j": f_local[5],
                "classification": classify_member_force(f_local),
            }
        )

    return rows


def classify_member_force(f_local):
    axial = max(abs(f_local[0]), abs(f_local[3]))
    shear = max(abs(f_local[1]), abs(f_local[4]))
    moment = max(abs(f_local[2]), abs(f_local[5]))

    if axial > shear and axial > moment:
        return "compression-dominant" if f_local[0] < 0 else "tension-dominant"

    if moment >= axial and moment >= shear:
        return "bending-dominant"

    return "mixed"
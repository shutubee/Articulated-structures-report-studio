def apply_basic_moment_releases(k_local, release_i=False, release_j=False):
    """
    Educational release handling for MVP. For production, use static condensation.
    """
    k = k_local.copy()
    tiny = 1e-9

    if release_i:
        dof = 2
        k[dof, :] = 0.0
        k[:, dof] = 0.0
        k[dof, dof] = tiny

    if release_j:
        dof = 5
        k[dof, :] = 0.0
        k[:, dof] = 0.0
        k[dof, dof] = tiny

    return k
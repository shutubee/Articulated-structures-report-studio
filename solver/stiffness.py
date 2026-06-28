import numpy as np


def frame_element_stiffness_2d(E, A, I, L):
    """Local 2D Euler-Bernoulli frame stiffness matrix."""
    if L <= 0:
        raise ValueError("Element length must be positive.")
    k = np.zeros((6, 6), dtype=float)
    EA_L = E * A / L
    EI = E * I

    k[0, 0] = EA_L
    k[0, 3] = -EA_L
    k[3, 0] = -EA_L
    k[3, 3] = EA_L

    k[1, 1] = 12 * EI / L**3
    k[1, 2] = 6 * EI / L**2
    k[1, 4] = -12 * EI / L**3
    k[1, 5] = 6 * EI / L**2

    k[2, 1] = 6 * EI / L**2
    k[2, 2] = 4 * EI / L
    k[2, 4] = -6 * EI / L**2
    k[2, 5] = 2 * EI / L

    k[4, 1] = -12 * EI / L**3
    k[4, 2] = -6 * EI / L**2
    k[4, 4] = 12 * EI / L**3
    k[4, 5] = -6 * EI / L**2

    k[5, 1] = 6 * EI / L**2
    k[5, 2] = 2 * EI / L
    k[5, 4] = -6 * EI / L**2
    k[5, 5] = 4 * EI / L
    return k


def transformation_matrix_2d(c, s):
    T = np.zeros((6, 6), dtype=float)
    T[0, 0] = c
    T[0, 1] = s
    T[1, 0] = -s
    T[1, 1] = c
    T[2, 2] = 1.0
    T[3, 3] = c
    T[3, 4] = s
    T[4, 3] = -s
    T[4, 4] = c
    T[5, 5] = 1.0
    return T


def transform_to_global(k_local, c, s):
    T = transformation_matrix_2d(c, s)
    return T.T @ k_local @ T
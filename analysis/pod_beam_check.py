"""Hand check for the STEVE pod studies: the pod as an Euler-Bernoulli beam (stalk + shell, smeared walls),
cantilevered at the hub collar. Same dimensions and smeared density as the STEVE part.

python3 pod_beam_check.py
"""
import math

import numpy as np

E, RHO = 73.1e9, 3398.0                     # Al 2219-T87 modulus; smeared density (pod mass / solid volume)
STALK = dict(L=6.25, r=0.590, t=0.020)      # mean radius, wall
POD = dict(L=20.30, r=2.010, t=0.040)
BULK_MASS = 2 * RHO * math.pi * 2.03 ** 2 * 0.06   # two end bulkheads, lumped at the pod ends


def section(p):
    A = 2 * math.pi * p["r"] * p["t"]
    I = math.pi * p["r"] ** 3 * p["t"]
    return A, I


def beam(n_stalk=30, n_pod=60):
    """Assemble a 2-node Hermite beam FE model; returns K, M (with the base clamped) and the node positions."""
    elems = []
    for p, n in ((STALK, n_stalk), (POD, n_pod)):
        A, I = section(p)
        for _ in range(n):
            elems.append((p["L"] / n, E * I, RHO * A))
    N = len(elems) + 1
    K = np.zeros((2 * N, 2 * N))
    M = np.zeros((2 * N, 2 * N))
    z = [0.0]
    for e, (le, EI, m) in enumerate(elems):
        k = EI / le ** 3 * np.array([[12, 6 * le, -12, 6 * le], [6 * le, 4 * le ** 2, -6 * le, 2 * le ** 2],
                                     [-12, -6 * le, 12, -6 * le], [6 * le, 2 * le ** 2, -6 * le, 4 * le ** 2]])
        mm = m * le / 420 * np.array([[156, 22 * le, 54, -13 * le], [22 * le, 4 * le ** 2, 13 * le, -3 * le ** 2],
                                      [54, 13 * le, 156, -22 * le], [-13 * le, -3 * le ** 2, -22 * le, 4 * le ** 2]])
        idx = [2 * e, 2 * e + 1, 2 * e + 2, 2 * e + 3]
        K[np.ix_(idx, idx)] += k
        M[np.ix_(idx, idx)] += mm
        z.append(z[-1] + le)
    # lumped bulkheads at the root and tip of the pod shell
    root = 2 * n_stalk                      # translational DOF of the stalk/pod junction node
    M[root, root] += BULK_MASS / 2
    M[-2, -2] += BULK_MASS / 2
    return K[2:, 2:], M[2:, 2:], np.array(z)


K, M, z = beam()
w2 = np.sort(np.real(np.linalg.eigvals(np.linalg.solve(M, K))))
f = np.sqrt(np.clip(w2, 0, None)) / (2 * math.pi)
mass = RHO * (section(STALK)[0] * STALK["L"] + section(POD)[0] * POD["L"]) + BULK_MASS
print(f"beam mass {mass / 1000:.1f} t (STEVE solid: 12.148 m³ × {RHO} = {12.148 * RHO / 1000:.1f} t)")
print("first bending frequencies (Hz):", ", ".join(f"{x:.3f}" for x in f[:3]))

# static: lateral tip force F (docking misalignment) -> stalk root bending stress and tip deflection
F_lat, F_ax = 5e3, 15e3
Ltot = STALK["L"] + POD["L"]
A_s, I_s = section(STALK)
M_root = F_lat * Ltot
sigma_b = M_root * (STALK["r"] + STALK["t"] / 2) / I_s
sigma_a = F_ax / A_s
f_vec = np.zeros(K.shape[0])
f_vec[-2] = F_lat
u = np.linalg.solve(K, f_vec)
print(f"docking case: root moment {M_root / 1e3:.0f} kN·m, stalk bending {sigma_b / 1e6:.1f} MPa + axial {sigma_a / 1e6:.2f} MPa, "
      f"tip deflection {u[-2] * 1000:.1f} mm")

# reboost / attitude: 0.05 m/s² lateral on the whole pod
a = 0.05
M_acc = sum(RHO * section(p)[0] * a * p["L"] * zc for p, zc in ((STALK, STALK["L"] / 2), (POD, STALK["L"] + POD["L"] / 2)))
M_acc += BULK_MASS / 2 * a * (STALK["L"] + Ltot)
print(f"0.05 m/s² lateral: root moment {M_acc / 1e3:.0f} kN·m, stalk bending {M_acc * 0.6 / I_s / 1e6:.2f} MPa")

# cabin pressure (real skin, not smeared): hoop stress p r / t
for t_skin in (0.0032, 0.004):
    print(f"pressure hoop stress, real {t_skin * 1000:.1f} mm skin: {101325 * 2.03 / t_skin / 1e6:.0f} MPa")

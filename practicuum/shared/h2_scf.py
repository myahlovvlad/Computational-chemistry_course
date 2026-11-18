"""Restricted Hartree-Fock for H2 in STO-3G, s functions only.

An educational implementation, NOT a general quantum-chemistry or DFT package.
STO-3G hydrogen coefficients: standard basis-set definition (BSE STO-3G).
All integral expressions use atomic units.
"""
from __future__ import annotations

from itertools import product
import math

import numpy as np
from scipy.linalg import eigh
from scipy.special import erf

EXPONENTS = np.array([3.42525091, 0.62391373, 0.16885540])
COEFFICIENTS = np.array([0.15432897, 0.53532814, 0.44463454])
ANGSTROM_TO_BOHR = 1.8897261254578281


def boys0(t: float) -> float:
    return 1.0 - t / 3.0 if t < 1e-9 else 0.5 * math.sqrt(math.pi / t) * erf(math.sqrt(t))


def matrices(distance_angstrom: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    if distance_angstrom <= 0:
        raise ValueError("A positive internuclear distance is required")
    centers = np.array([[0., 0., 0.], [0., 0., distance_angstrom * ANGSTROM_TO_BOHR]])
    weights = COEFFICIENTS * (2 * EXPONENTS / math.pi) ** 0.75
    s, h, eri = np.zeros((2, 2)), np.zeros((2, 2)), np.zeros((2, 2, 2, 2))
    for i, j in product(range(2), repeat=2):
        a_center, b_center = centers[i], centers[j]
        ab2 = np.dot(a_center-b_center, a_center-b_center)
        for ia, ib in product(range(3), repeat=2):
            a, b = EXPONENTS[ia], EXPONENTS[ib]
            p, mu = a+b, a*b/(a+b)
            pc = (a*a_center+b*b_center)/p
            kab = math.exp(-mu*ab2)
            weight = weights[ia]*weights[ib]
            overlap = (math.pi/p)**1.5 * kab
            kinetic = mu*(3-2*mu*ab2)*overlap
            attraction = sum(-2*math.pi/p*kab*boys0(p*np.dot(pc-c, pc-c)) for c in centers)
            s[i,j] += weight*overlap
            h[i,j] += weight*(kinetic+attraction)
    for i, j, k, l in product(range(2), repeat=4):
        ac, bc, cc, dc = centers[[i,j,k,l]]
        ab2, cd2 = np.dot(ac-bc,ac-bc), np.dot(cc-dc,cc-dc)
        for ia, ib, ic, id_ in product(range(3), repeat=4):
            a,b,c,d = EXPONENTS[[ia,ib,ic,id_]]
            p,q = a+b,c+d
            pc,qc = (a*ac+b*bc)/p,(c*cc+d*dc)/q
            factor = 2*math.pi**2.5/(p*q*math.sqrt(p+q))
            integral = factor*math.exp(-a*b/p*ab2-c*d/q*cd2)*boys0(p*q/(p+q)*np.dot(pc-qc,pc-qc))
            eri[i,j,k,l] += np.prod(weights[[ia,ib,ic,id_]])*integral
    return s, h, eri, 1/np.linalg.norm(centers[0]-centers[1])


def rhf_h2(distance_angstrom: float = 0.74, max_cycles: int = 50, tolerance: float = 1e-10) -> dict:
    s,h,eri,enuc = matrices(distance_angstrom)
    _, coefficients = eigh(h,s)
    density = 2*np.outer(coefficients[:,0],coefficients[:,0])
    previous = None
    trace = []
    for cycle in range(1,max_cycles+1):
        coulomb = np.einsum('kl,ijkl->ij', density, eri)
        exchange = np.einsum('kl,ikjl->ij', density, eri)
        fock = h+coulomb-0.5*exchange
        _, coefficients = eigh(fock,s)
        new_density = 2*np.outer(coefficients[:,0],coefficients[:,0])
        energy = float(0.5*np.sum(density*(h+fock))+enuc)
        change = float(np.linalg.norm(new_density-density))
        trace.append({"cycle":cycle,"energy_hartree":energy,"density_change":change})
        if previous is not None and abs(energy-previous)<tolerance and change<tolerance:
            return {"distance_angstrom":distance_angstrom,"energy_hartree":energy,
                    "converged":True,"cycles":cycle,"trace":trace,
                    "method":"RHF/STO-3G; restricted H2 only"}
        previous,density = energy,new_density
    raise RuntimeError("SCF did not converge")


if __name__ == '__main__':
    print(rhf_h2())

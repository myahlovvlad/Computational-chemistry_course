"""Lossless token formatting for PDB2PQR/Meeko interoperability."""
import math
import re


def normalize_pqr(text,*,canonical_resnames=False):
    lines=[]
    for line in text.splitlines():
        if not line.startswith(('ATOM','HETATM')):continue
        fields=line.split()
        if len(fields)==10:
            combined=re.fullmatch(r'([A-Za-z])(-?\d+)',fields[4])
            if combined:fields[4:5]=list(combined.groups())
        if len(fields) not in {10,11}:raise ValueError('Unexpected PQR atom record length')
        if int(fields[1])<=0:raise ValueError('Invalid atom serial')
        int(fields[-6])  # residue number, with or without a separate chain field
        if not all(math.isfinite(float(v)) for v in fields[-5:]):raise ValueError('Nonfinite PQR coordinate, charge or radius')
        # AMBER deliberately assigns zero radii to some hydrogens. Preserve it.
        if float(fields[-1])<0:raise ValueError('Negative PQR radius')
        if canonical_resnames:
            # Meeko's HIS ambiguity table includes terminal CHID/CHIE/CHIP.
            # Specialized AMBER HID labels otherwise force a nonterminal template.
            # Atom names, protons and read charges remain unchanged.
            fields[3]={'HID':'HIS','HIE':'HIS','HIP':'HIS'}.get(fields[3],fields[3])
        lines.append(' '.join(fields))
    if not lines:raise ValueError('No PQR atom records')
    return '\n'.join(lines)+'\n'

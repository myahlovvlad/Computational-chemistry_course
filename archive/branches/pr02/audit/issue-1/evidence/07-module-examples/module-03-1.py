from chemistry import standardize
record = standardize("CC(=O)[O-].[Na+]")
print(record.raw_smiles, record.parent_smiles, record.policy)
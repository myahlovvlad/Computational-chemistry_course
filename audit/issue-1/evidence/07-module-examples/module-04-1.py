from chemistry import standardize, descriptors
record = standardize("CCO")
print(descriptors(record.parent_smiles))
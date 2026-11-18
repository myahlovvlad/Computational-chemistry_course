def to_molar(value: float, scale: float) -> float:
    # WHY: логарифм концентрации требует единой системы единиц.
    return value * scale

values = [10.0, 100.0, 1000.0]
result = [to_molar(value, 1e-9) for value in values]
print(result)
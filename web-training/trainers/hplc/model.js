window.HPLC_MODEL = {
  "source_doi": "10.3390/molecules18032469",
  "attribution": "Crevar-Sakač, Vujić, Brborić, Kuntić, Uskoković-Marković (2013), Table 1; CC BY 3.0",
  "input_sha256": "48f2e1cde1995d8419cb27c67484e16fd8c3c767675dcf142b0ae4994adfbb4c",
  "method": "own full quadratic ordinary least squares refit; not exact reconstruction of published reduced models",
  "factor_order": [
    "acetonitrile_percent",
    "column_temperature_C",
    "flow_mL_min"
  ],
  "center": [
    65,
    35,
    1
  ],
  "scale": [
    5,
    5,
    0.2
  ],
  "terms": [
    "1",
    "a",
    "b",
    "c",
    "a*b",
    "a*c",
    "b*c",
    "a*a",
    "b*b",
    "c*c"
  ],
  "response_order": [
    "retention_p_ATO_min",
    "retention_ATO_lactone_min"
  ],
  "coefficients": [
    [
      2.8410545454545453,
      7.268463636363636
    ],
    [
      -0.20399999999999996,
      -0.13369999999999987
    ],
    [
      -0.4719999999999995,
      -0.40419999999999945
    ],
    [
      0.3770999999999997,
      0.3257999999999998
    ],
    [
      -0.3835000000000019,
      -0.5477500000000013
    ],
    [
      0.052500000000000095,
      -0.5057499999999998
    ],
    [
      0.10649999999999998,
      0.19775000000000012
    ],
    [
      -0.7926363636363631,
      -0.43590909090909
    ],
    [
      -0.16863636363636364,
      -0.2714090909090905
    ],
    [
      0.09886363636363657,
      0.5995909090909098
    ]
  ],
  "rank": 10,
  "n": 20,
  "training_RMSE_min": [
    0.12434846930373457,
    0.1672698907862271
  ],
  "validation": "in-sample fit only; independent validation NOT_RUN",
  "fixed_conditions": {
    "pH": 4.6,
    "column": "ZORBAX Eclipse Plus C18 250 x 4.6 mm, 5 um",
    "elution": "isocratic",
    "detector_nm": 254,
    "sample_matrix": "Wistar rat plasma"
  },
  "observations": [
    {
      "acetonitrile_percent": 65.0,
      "column_temperature_C": 35.0,
      "flow_mL_min": 1.0,
      "retention_p_ATO_min": 2.851,
      "retention_ATO_lactone_min": 6.982,
      "symmetry_p_ATO": 1.183,
      "symmetry_o_ATO": 1.122,
      "symmetry_ATO": 1.132,
      "symmetry_ATO_lactone": 1.102,
      "relative_retention_p_ATO": 1.102
    },
    {
      "acetonitrile_percent": 65.0,
      "column_temperature_C": 35.0,
      "flow_mL_min": 1.0,
      "retention_p_ATO_min": 2.856,
      "retention_ATO_lactone_min": 7.089,
      "symmetry_p_ATO": 1.146,
      "symmetry_o_ATO": 1.098,
      "symmetry_ATO": 1.107,
      "symmetry_ATO_lactone": 1.121,
      "relative_retention_p_ATO": 1.126
    },
    {
      "acetonitrile_percent": 65.0,
      "column_temperature_C": 30.0,
      "flow_mL_min": 1.0,
      "retention_p_ATO_min": 3.158,
      "retention_ATO_lactone_min": 7.445,
      "symmetry_p_ATO": 0.753,
      "symmetry_o_ATO": 0.779,
      "symmetry_ATO": 0.872,
      "symmetry_ATO_lactone": 0.979,
      "relative_retention_p_ATO": 1.213
    },
    {
      "acetonitrile_percent": 65.0,
      "column_temperature_C": 35.0,
      "flow_mL_min": 1.0,
      "retention_p_ATO_min": 2.874,
      "retention_ATO_lactone_min": 7.251,
      "symmetry_p_ATO": 1.128,
      "symmetry_o_ATO": 1.168,
      "symmetry_ATO": 1.232,
      "symmetry_ATO_lactone": 1.246,
      "relative_retention_p_ATO": 1.207
    },
    {
      "acetonitrile_percent": 65.0,
      "column_temperature_C": 35.0,
      "flow_mL_min": 1.0,
      "retention_p_ATO_min": 3.214,
      "retention_ATO_lactone_min": 7.861,
      "symmetry_p_ATO": 1.047,
      "symmetry_o_ATO": 1.119,
      "symmetry_ATO": 1.206,
      "symmetry_ATO_lactone": 1.123,
      "relative_retention_p_ATO": 1.143
    },
    {
      "acetonitrile_percent": 70.0,
      "column_temperature_C": 30.0,
      "flow_mL_min": 1.2,
      "retention_p_ATO_min": 2.905,
      "retention_ATO_lactone_min": 7.652,
      "symmetry_p_ATO": 0.441,
      "symmetry_o_ATO": 0.503,
      "symmetry_ATO": 0.427,
      "symmetry_ATO_lactone": 0.913,
      "relative_retention_p_ATO": 0.556
    },
    {
      "acetonitrile_percent": 60.0,
      "column_temperature_C": 35.0,
      "flow_mL_min": 1.0,
      "retention_p_ATO_min": 2.134,
      "retention_ATO_lactone_min": 7.128,
      "symmetry_p_ATO": 1.148,
      "symmetry_o_ATO": 1.204,
      "symmetry_ATO": 0.986,
      "symmetry_ATO_lactone": 0.998,
      "relative_retention_p_ATO": 1.162
    },
    {
      "acetonitrile_percent": 65.0,
      "column_temperature_C": 35.0,
      "flow_mL_min": 0.8,
      "retention_p_ATO_min": 2.302,
      "retention_ATO_lactone_min": 7.636,
      "symmetry_p_ATO": 0.897,
      "symmetry_o_ATO": 0.962,
      "symmetry_ATO": 1.165,
      "symmetry_ATO_lactone": 0.946,
      "relative_retention_p_ATO": 1.237
    },
    {
      "acetonitrile_percent": 65.0,
      "column_temperature_C": 35.0,
      "flow_mL_min": 1.0,
      "retention_p_ATO_min": 2.826,
      "retention_ATO_lactone_min": 7.241,
      "symmetry_p_ATO": 1.147,
      "symmetry_o_ATO": 1.201,
      "symmetry_ATO": 1.136,
      "symmetry_ATO_lactone": 1.121,
      "relative_retention_p_ATO": 1.145
    },
    {
      "acetonitrile_percent": 70.0,
      "column_temperature_C": 30.0,
      "flow_mL_min": 0.8,
      "retention_p_ATO_min": 2.342,
      "retention_ATO_lactone_min": 8.359,
      "symmetry_p_ATO": 0.595,
      "symmetry_o_ATO": 0.436,
      "symmetry_ATO": 0.661,
      "symmetry_ATO_lactone": 0.626,
      "relative_retention_p_ATO": 1.362
    },
    {
      "acetonitrile_percent": 60.0,
      "column_temperature_C": 40.0,
      "flow_mL_min": 0.8,
      "retention_p_ATO_min": 1.764,
      "retention_ATO_lactone_min": 6.352,
      "symmetry_p_ATO": 0.432,
      "symmetry_o_ATO": 0.553,
      "symmetry_ATO": 0.614,
      "symmetry_ATO_lactone": 0.661,
      "relative_retention_p_ATO": 1.245
    },
    {
      "acetonitrile_percent": 60.0,
      "column_temperature_C": 30.0,
      "flow_mL_min": 0.8,
      "retention_p_ATO_min": 2.089,
      "retention_ATO_lactone_min": 6.452,
      "symmetry_p_ATO": 0.559,
      "symmetry_o_ATO": 0.651,
      "symmetry_ATO": 0.801,
      "symmetry_ATO_lactone": 0.867,
      "relative_retention_p_ATO": 1.268
    },
    {
      "acetonitrile_percent": 60.0,
      "column_temperature_C": 30.0,
      "flow_mL_min": 1.2,
      "retention_p_ATO_min": 2.453,
      "retention_ATO_lactone_min": 7.753,
      "symmetry_p_ATO": 0.982,
      "symmetry_o_ATO": 0.812,
      "symmetry_ATO": 0.806,
      "symmetry_ATO_lactone": 0.995,
      "relative_retention_p_ATO": 0.585
    },
    {
      "acetonitrile_percent": 70.0,
      "column_temperature_C": 40.0,
      "flow_mL_min": 1.2,
      "retention_p_ATO_min": 1.472,
      "retention_ATO_lactone_min": 6.152,
      "symmetry_p_ATO": 1.284,
      "symmetry_o_ATO": 0.993,
      "symmetry_ATO": 0.898,
      "symmetry_ATO_lactone": 0.962,
      "relative_retention_p_ATO": 0.565
    },
    {
      "acetonitrile_percent": 65.0,
      "column_temperature_C": 40.0,
      "flow_mL_min": 1.0,
      "retention_p_ATO_min": 1.976,
      "retention_ATO_lactone_min": 6.573,
      "symmetry_p_ATO": 1.112,
      "symmetry_o_ATO": 1.085,
      "symmetry_ATO": 0.903,
      "symmetry_ATO_lactone": 1.011,
      "relative_retention_p_ATO": 1.082
    },
    {
      "acetonitrile_percent": 60.0,
      "column_temperature_C": 40.0,
      "flow_mL_min": 1.2,
      "retention_p_ATO_min": 2.543,
      "retention_ATO_lactone_min": 8.459,
      "symmetry_p_ATO": 1.052,
      "symmetry_o_ATO": 1.021,
      "symmetry_ATO": 0.984,
      "symmetry_ATO_lactone": 0.924,
      "relative_retention_p_ATO": 0.581
    },
    {
      "acetonitrile_percent": 70.0,
      "column_temperature_C": 35.0,
      "flow_mL_min": 1.0,
      "retention_p_ATO_min": 1.752,
      "retention_ATO_lactone_min": 6.561,
      "symmetry_p_ATO": 1.064,
      "symmetry_o_ATO": 1.011,
      "symmetry_ATO": 1.006,
      "symmetry_ATO_lactone": 0.922,
      "relative_retention_p_ATO": 1.151
    },
    {
      "acetonitrile_percent": 65.0,
      "column_temperature_C": 35.0,
      "flow_mL_min": 1.0,
      "retention_p_ATO_min": 2.847,
      "retention_ATO_lactone_min": 7.139,
      "symmetry_p_ATO": 1.152,
      "symmetry_o_ATO": 1.117,
      "symmetry_ATO": 1.127,
      "symmetry_ATO_lactone": 1.098,
      "relative_retention_p_ATO": 1.142
    },
    {
      "acetonitrile_percent": 70.0,
      "column_temperature_C": 40.0,
      "flow_mL_min": 0.8,
      "retention_p_ATO_min": 0.472,
      "retention_ATO_lactone_min": 6.083,
      "symmetry_p_ATO": 1.109,
      "symmetry_o_ATO": 0.595,
      "symmetry_ATO": 0.685,
      "symmetry_ATO_lactone": 0.538,
      "relative_retention_p_ATO": 1.365
    },
    {
      "acetonitrile_percent": 65.0,
      "column_temperature_C": 35.0,
      "flow_mL_min": 1.2,
      "retention_p_ATO_min": 3.367,
      "retention_ATO_lactone_min": 8.124,
      "symmetry_p_ATO": 1.203,
      "symmetry_o_ATO": 1.206,
      "symmetry_ATO": 1.167,
      "symmetry_ATO_lactone": 1.121,
      "relative_retention_p_ATO": 0.536
    }
  ],
  "figure5_annotated_Rt_min": {
    "p_ATO": 3.052,
    "o_ATO": 4.78,
    "ATO": 5.445,
    "ATO_lactone": 7.064
  },
  "figure5_conditions": {
    "ACN_percent": 61.93,
    "temperature_C": 31.44,
    "flow_mL_min": 1.03
  },
  "figure5_scope": "one published chromatogram; annotations are not numeric raw traces or a fitted model of middle peaks",
  "limitations": [
    "no numeric raw chromatograms",
    "no baseline peak widths",
    "middle-peak positions outside the single figure condition are assumptions",
    "all Gaussian profiles and widths in the trainer are explicit teaching simulations",
    "no pH/gradient/column response calibration",
    "Rs alone does not establish method validation"
  ]
};

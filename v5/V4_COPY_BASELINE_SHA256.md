# V4 copy baseline for V5

- Captured: 2026-08-26T19:07+09:00
- Source: `v4/`
- Target: `v5/`
- Excluded: `VERIFICATION.md`, `__pycache__/`, `tests/__pycache__/`, `runtime/notice_extraction_cache.sqlite`, server logs, and temporary test artifacts
- Corresponding files: 16
- Immediate SHA-256 matches: 16/16 (100%)

| V4 relative path | SHA-256 |
| --- | --- |
| `__init__.py` | `8c496a91435facbb36381c86a88418ced8e994ec048adf97dc928493de4ae694` |
| `main.py` | `530afa8c003eaf0e3c63e9038024cc83c28e71ce4ff3e0b37471248e97017c34` |
| `orchestrator.py` | `6ed035faf52c8e0ff5c32a80128c00f900f55fc6a1a4a981c5d2d7b66b6d3a89` |
| `copilot.py` | `94210fb463ee6d98849a95b65f455fd61acb5144683bb5d507010f1f0ccb4755` |
| `README.md` | `2a4af6d402e09680d2f953f0cd242713cfa6ceac9bdf167c0b70aca8bc5e1d49` |
| `static/index.html` | `ae2a2bc823f2e7e4eb59d1864ce853a05f4016e14003ee96e67ebf0c591d1055` |
| `static/app.js` | `502f842453cc9db191c4b840eefd7feae8d6e902944ba3e87259c980a682f218` |
| `static/styles.css` | `83c8d80ab3348382057ed65c3f2c3381daa353760ec230a6b6298d0c2d461c71` |
| `static/v3-extension.css` | `59b909838fd6cf806f1aa6cfe708d49eb022b9c34838fd1d5e6ecfa5da402666` |
| `static/v4-extension.css` | `c6e85113f12781fda6a5af16fafdb2caf2ca127685a35d166175398b3d8cd28a` |
| `static/v4-extension.js` | `063d627c515a0fb271cc06645ea815d2fe54a7d18897d776a0c4e734944383b5` |
| `static/templates/거래내역_입력양식.csv` | `9f5949f4a7a06ae6dd1cb6bfbba7c8f518bf5caaf4b176403c2d1a9e1e59f76b` |
| `static/templates/대출_입력양식.csv` | `8cf886206873e9a35786131a09913a4b48006caa9b3c888670157fb363123189` |
| `tests/test_v4.py` | `6bfb40b5f3e82f5ad00bd7cf9711647d35d48a7500702a45c214b799df1af0ae` |
| `V2_BASELINE_SHA256.md` | `a2d920c1cc1c580c747b1e8201f52da386f6e92270cca48c57e56e872de6f04a` |
| `V3_COPY_BASELINE_SHA256.md` | `bb342cf0a021e6d6f6fe6ae41332c2d94f72d94392824e7293bf513a716bf805` |

## Planned V5-only renames

- `v5/static/v4-extension.css` to `v5/static/v5-extension.css`
- `v5/static/v4-extension.js` to `v5/static/v5-extension.js`
- `v5/tests/test_v4.py` to `v5/tests/test_v5.py`

This baseline records the bytes immediately after copying and before any V5 edit or rename.

# Insumos_Control_Polizas

This is a data/document repository, not a code project. There is no source code, package manager, build/test/lint tooling, CI, or entrypoint to run.

## Contents

- `Maestro_Clientes.xlsx` — master client data at the repo root.
- `polizas/` — 20 insurance policy PDFs named `Poliza_{TYPE}-2026-{NNNN}.pdf`.
  - Policy types seen: `AIS`, `PCS`, `SPC`.
  - Example: `Poliza_PCS-2026-0001.pdf`, `Poliza_AIS-2026-0001.pdf`, `Poliza_SPC-2026-0001.pdf`.

## Guidance for agents

- Do not look for code to compile, tests to run, or a dev server — none exist here.
- Do not assume `polizas/` is a package; it is a folder of PDF documents.
- If you need to inspect policy content, open the PDFs directly; there is no codegen or extraction pipeline.
- If you add files, keep them under `polizas/` (PDFs) or root-level data files; do not introduce build/config scaffolding unless the repo's purpose changes.

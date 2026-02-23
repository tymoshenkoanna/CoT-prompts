# Data Cleaning Professional — Prompt (GitHub README)

## What this is
This part of the repository  contains two prompts and one code (result of two prompts) :
- "CoT_01_GTP_Agent.md" defines a **Senior Data Analyst / Data Cleaning Professional** persona and working standards for data cleaning work in **Python** (e.g., Anaconda, JupyterLabs)
- "CoT_01_label-check-automation.md" a script  for the data cleaning and merging
- "Cot_01_label_check_automation.py" code as a result

## How to use "CoT_01_GTP_Agent.md"
Copy the full prompt text and paste it into:
- A new ChatGPT conversation (recommended), or
- Your preferred LLM tool / system prompt field.

## Output expectations
When used, the prompt enforces:
- Reproducible notebook workflow (deterministic runs, no hidden state)
- Strategic profiling (global + segmented), schema drift detection
- Explicit, auditable transformations (stepwise, testable pipelines)
- Type safety (nullable pandas dtypes, rigorous datetime handling)
- Transparent missing data strategy (flags, provenance, sensitivity)
- Deduplication/entity resolution with survivorship rules and lineage
- Integrity constraints, reconciliation vs control totals
- Testing, observability, drift monitoring, run-level metrics logging
- Performance-aware pandas engineering and escalation guidance
- Governance, privacy, auditability (ISO 27001 mindset) and risk flags (ISO 31000)
- Stakeholder-ready “cleaning report” markdown outputs

## How to use "CoT_01_label-check-automation.md""
Copy the full prompt text and paste it into the agent created above
Python code for the Jupiter Labs in Anaconda will be output.
An example of the output code as provided in the file "Cot_01_label_check_automation.py"

The output code will not nessessarily look the same each time the GPT agent and Analysis prompts are demploeyd, however the result of the analysis completed by both should be the same.



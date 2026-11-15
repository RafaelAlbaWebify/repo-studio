# Repo Studio — Evidence-first benchmark protocol

This is a **measurement template**, not a claim that Repo Studio saves tokens.

## Protocol

1. Select 10 representative, reproducible legacy-code investigations, including at least two where the tool may provide little value. Record the repository commit and the expected investigation question separately; never publish private code.
2. For each case, run **baseline** (normal AI-assisted repo investigation) and **repo_studio** (user-selected evidence pack) under the same model/version, instructions, quality rubric, and reasonable investigation conditions. Counterbalance the order where possible.
3. Record actual **total input and output tokens across all turns and follow-ups**, including any tool-context messages counted by the provider. Record elapsed time and number of follow-ups. Use provider usage records; do not substitute characters/4 for tokens.
4. Independently judge whether the answer identifies relevant source lines, limitations and an appropriately cautious conclusion; a useful answer must not assert safe refactoring without adequate proof.
5. Fill `results.csv`. Missing measures stay blank. `quality_pass` is `yes` or `no`; cases missing measurements are excluded, not silently counted as successes.
6. Run `python3 benchmark/measure.py benchmark/results.csv --output benchmark/summary.json` from the application directory. Do not publish confidential prompts or repository source in the summary.

A fair interpretation compares **quality-matched pairs**; also report failure cases and explain exclusions. This benchmark does not isolate the effect of the UI from changes in user strategy.

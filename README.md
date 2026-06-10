# MAS-Debate — LLM-based Multi-Agent Debate Platform

A research platform for simulating debates with LLM-based multi-agent systems. Teams argue a motion in front of an audience that votes before and after the debate. The platform provides formal reasoning and transparent scaffolding to structure each agent's argumentation, and supports several reasoning architectures (e.g. Chain-of-Thought, Tree-of-Thought, GODSAF, reflection and tool-augmented variants) so they can be compared on quality and cost.

## Publications

This platform was built for and used to run the experiments in the following articles:

- **Simulating Oxford-Style Debates with LLM-based Multi-Agent Systems** — full paper at the
  *17th Asian Conference on Intelligent Information and Database Systems (ACIIDS 2025)*,
  23–25 April 2025, Kitakyushu, Japan (Springer Nature Singapore). Published in the official
  proceedings: https://doi.org/10.1007/978-981-96-6008-7_21

- **Formal Reasoning and Guidance Platform for Transparent Scaffolding for Multi-Agent
  Debate** — accepted at the *8th International Conference on Computational Collective
  Intelligence (ICCCI 2026)*, 23–25 September 2026, Heraklion, Greece. To appear in the
  conference proceedings via SpringerLink.

- **Cost-Quality Trade-offs in Reasoning Architectures for Agentic Software Engineering
  Deliberation** — short paper at the *52nd Euromicro Conference on Software Engineering and
  Advanced Applications (SEAA 2026)*, 2–4 September 2026, Kraków, Poland. To be published by
  Springer in the *Lecture Notes in Computer Science (LNCS)* series via SpringerLink.

## Repository layout

| Path | Description |
|------|-------------|
| `src/` | Core platform: debate teams (`team`, `team_extended` — CoT / ToT / GoDsAF members), `audience`, `chairman`, `debate` orchestration, `reasoning` (ASP / GoDsAF / miner), `hub` (LLM, embeddings, search), `tutor` (argument-quality evaluation), `utils` |
| `scripts/` | Experiment running and analysis: `run_architecture_tests.py`, `analyze_architecture_results.py`, `evaluate_argument_quality.py`, `statistical_analysis.py`, Pareto / cost-quality analysis and plotting |
| `configs/` | Debate configurations |

## Setup

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.template .env
```

## Running experiments

Experiments are driven by JSON config files that define the motion, teams, reasoning architectures, and audience. Run a single config or a whole folder:

```bash
# Run one configuration
python scripts/run_architecture_tests.py --config configs/se/medium/microservices_vs_monoliths.json

# Run every config in a folder
python scripts/run_architecture_tests.py --folder configs/se/medium/

# Optional: choose where results are written
python scripts/run_architecture_tests.py --folder configs/se/medium/ --output-dir my_results/
```

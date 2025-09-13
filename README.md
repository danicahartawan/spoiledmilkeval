# Exa Spoiled Milk Evaluation

A comprehensive evaluation comparing Exa's neural search against baseline systems for deprecated technology queries.

## Overview

The "Spoiled Milk" evaluation tests how well different search systems help developers find information about deprecated technologies and their alternatives. Like spoiled milk, deprecated technologies need to be replaced quickly with fresh alternatives.

**30 real-world deprecation queries** across three frameworks:
- **Next.js** (10 queries): getInitialProps → getServerSideProps, Image layout prop, App Router migrations
- **PyTorch** (10 queries): autograd.Function patterns, volatile tensors, CUDA streams  
- **TensorFlow** (10 queries): tf.contrib removals, Session → eager execution, optimizer renames

**Systems Evaluated:**
- **Exa**: Neural search with semantic understanding
- **Google**: Traditional keyword search via Custom Search API
- **StackOverflow**: Domain-specific search via StackOverflow API  
- **Claude**: LLM-generated recommendations with citations

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API keys:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys (minimum: EXA_API_KEY)
   ```

3. **Run full evaluation:**
   ```bash
   python -m src.eval_runner
   ```

4. **View results:**
   ```bash
   cat reports/summary.md
   ```

## Setup Requirements

### Required
- **EXA_API_KEY**: Get from [exa.ai](https://exa.ai/)

### Optional (for specific baselines)
- **GOOGLE_SEARCH_API_KEY** + **GOOGLE_SEARCH_ENGINE_ID**: [Google Custom Search](https://cse.google.com/)
- **ANTHROPIC_API_KEY**: [Anthropic Console](https://console.anthropic.com/) (for Claude baseline)
- **STACKOVERFLOW_API_KEY**: [StackApps](https://stackapps.com/) (higher rate limits)

## Evaluation Metrics

Four metrics evaluate deprecation search quality:

### 1. Deprecation@k (0.0-1.0)
Detects deprecation language in top-k results using regex patterns:
- "deprecated", "removed", "replaced", "migration guide", "instead"

### 2. Replacement Coverage (0.0-1.0)  
Measures presence of replacement guidance:
- "use X instead", "migrate to Y", "recommended alternative"

### 3. Authority@k (1-3)
Maximum authority tier among top-k results:
- **Tier 3**: Official docs (`nextjs.org`, `pytorch.org`, GitHub org repos)
- **Tier 2**: GitHub issues, StackOverflow, company blogs
- **Tier 1**: Personal blogs, tutorials, general content

### 4. Time-to-Solution (rank or ∞)
Rank of first result meeting ALL criteria:
- Contains deprecation language + replacement guidance + authority ≥2

## Repository Structure

```
spoiledmilkeval_danica/
├── README.md                 # This file
├── requirements.txt          # Python dependencies  
├── .env.example             # Environment template
├── data/
│   ├── queries.jsonl        # 30 curated deprecation queries
│   └── labels.schema.json   # Evaluation rubric
├── src/
│   ├── eval_runner.py       # Main evaluation orchestrator
│   ├── exa_client.py        # Exa API wrapper + caching
│   ├── metrics.py           # 4 core metrics implementation
│   ├── utils.py             # Authority scoring, caching utilities
│   └── baselines/
│       ├── result.py        # Result data structure
│       ├── google.py        # Google Custom Search baseline
│       ├── stackoverflow.py # StackOverflow API baseline
│       └── claude.py        # Claude API baseline
├── tests/                   # Unit tests for metrics
├── results/                 # Generated: individual result files (git-ignored)
└── reports/
    └── summary.md          # Latest evaluation summary
```

## Usage Examples

**Test setup with minimal queries:**
```bash
python -c "
from src.eval_runner import EvalRunner
runner = EvalRunner()
queries = runner.load_queries()[:2]  # Test with 2 queries
print(f'Loaded {len(queries)} queries')
"
```

**Run single system:**
```bash
# Export only EXA_API_KEY in .env
python -m src.eval_runner
```

**Test-run framework:**
```bash
python -m pytest tests/ -v
```

## Results & Interpretation

After running evaluation, check `reports/summary.md` for:
- **Overall system ranking** by weighted effectiveness score
- **Per-framework performance** (Next.js, PyTorch, TensorFlow breakdown)
- **Detailed metrics** for each system
- **Success rates** and statistical summaries

## Security Notes

- **.env file**: Contains API keys, never commit to git (.gitignore protects this)
- **No secrets in code**: All API keys loaded from environment variables
- **Generated files**: results/ and reports/ contain no sensitive data

## Reproducibility

- **Caching**: API responses cached in `.cache/` (git-ignored) for consistent re-runs
- **Deterministic**: Same queries + API keys = same results
- **Timestamps**: All result files timestamped for multiple evaluation runs

## Limitations

- **API Dependencies**: Some baselines require external API keys and may hit rate limits  
- **Query Scope**: 30 queries focused on 3 frameworks (Next.js, PyTorch, TensorFlow)
- **Authority Scoring**: Domain-based heuristic, may need manual curation for specialized domains
- **Language Patterns**: Replacement detection uses regex heuristics vs. semantic understanding

## Development

Run tests before changes:
```bash
python -m pytest tests/test_metrics.py -v       # Core metrics
python -m pytest tests/test_authority_score.py -v # Authority scoring  
python -m pytest tests/test_utils.py -v         # Utilities
```

## Citation

```bibtex
@misc{spoiled-milk-eval-2024,
  title={Spoiled Milk: Evaluating Search Systems for Deprecated Technology Queries},
  year={2024},
  note={Exa evaluation framework}
}
```
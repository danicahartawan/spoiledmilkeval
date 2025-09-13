# Exa & the Spoiled Milk Problem

By Danica Hartawan

A comprehensive evaluation comparing Exa's neural search against baseline systems for deprecated technology queries.

## Why this exists

When I was evolving Metric into Toko (a feedback assistant that lives in-app), I kept hitting the same wall: deprecated APIs. Code that shipped last quarter silently broke, and searching for answers just made things worse.

StackOverflow threads, random blogs, and even framework docs looked fine at first glance-like grabbing milk from the fridge that looks okay-until they quietly ruined my workflow. That's the spoiled milk problem. 

This repo asks a simple but customer-convincing question: If Google and Bing keep serving spoiled milk, can Exa prove it's always surfacing the fresh, authoritative replacement first?

## What I did

I used the CUPS/product circles framework: clarify → users → needs → prioritization → solutions → metrics.

1. Clarify: Developers waste hours on stale answers about deprecated APIs.

2. Users:
- Developers (migrating frameworks, debugging breaking changes)
- AI agents/model builders (need authoritative replacements, not stale docs)
- Enterprise teams (care about stability and reliability)

Needs:
- Early recognition of deprecations
- Clear replacement guidance
- Authority (official docs > GitHub issues > StackOverflow > blogs)

## Scope & Setup

**30 real-world deprecation queries** across three frameworks:
- **Next.js** (10 queries): getInitialProps → getServerSideProps, Image layout prop, App Router migrations
- **PyTorch** (10 queries): autograd.Function patterns, volatile tensors, CUDA streams  
- **TensorFlow** (10 queries): tf.contrib removals, Session → eager execution, optimizer renames

**Systems Evaluated:**
- **Exa**: Neural search with semantic understanding (otw to being the best)
- **Google**: Traditional keyword search via Custom Search API (an obvious choice)
- **StackOverflow**: Domain-specific search via StackOverflow API (never tried but heard through reddit, pretty cool!)
- **Claude**: LLM-generated recommendations with citations (spoiler alert, this one did the best)

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

## What I Learned

- Iteration is sososo messy: I burned time on over-broad queries, broken Claude calls, and mismatched authority scoring. Each mistake forced me to simplify and refocus.
- AI as a co-pilot: About half my code came from ChatGPT (i've tested a lot of llms and this one worked the best for prompts), but I never copy-pasted. I treated it like an editor—drafts came from AI, judgment calls came from me.
- Research mindset (asking the right questions aka what I believe is my strength): I stalked Exa's repos, docs, YouTube talks, podcasts, and even Reddit threads. That made sure this eval wasn't abstract-it was tied to real use cases developers care about.
- Bias for action vs. hygiene: I pushed too fast and accidentally committed .env keys after a retreat. Fixed it by rotating keys, cleaning the repo, and adding guardrails. Early speed mattered, but cleanup taught me discipline (sadly).

## Why This Matters

If I can show Exa wins this benchmark—even on a small set of queries—it's directly convincing to customers. Developers don't want spoiled milk. They want to know:
1. What broke 
2. then, What to use instead
3. From an authoritative source (like exa)

That's the value I believe Exa can own!

## Future Extensions (If I Had More Time)

This repo is scoped to ~12-20h, but here's where I'd take it further:

1. Expand Framework Coverage
Add more ecosystems where deprecations move fast: React/Angular, Hugging Face, Kubernetes APIs.
2. Automated Query Generation
Right now I hand-curated 30 queries. With more time, I'd scrape GitHub issues, changelogs, and release notes to auto-generate fresh deprecation queries weekly; this would keep the benchmark living and continuously valuable.
3. Agent Workflow Simulation
Instead of static queries, we can build an agent harness that tries to fix code using different search APIs.
4. Long-Tail Vertical Tests
We can explore niche but high-value areas (medical AI libraries, enterprise APIs, financial compliance SDKs).

OVERALL JUST EXCITED ABOUT WHAT'S NEXT FOR EXA'S EVALS

## What This Evaluation Reveals About Exa's API

Based on running this eval, here's what I think Exa could improve to dominate the deprecation search space:

### 🎯 **Major Opportunities**

**1. Replacement Guidance Detection**
- **Current:** 36.7% replacement coverage vs Claude's 53.3%
- **Issue:** Exa finds deprecated content but struggles to surface "what to use instead"
- **API Improvement:** Add semantic understanding for migration/replacement language patterns, boost results containing "instead of", "migrate to", "replaced by"

**2. Complete Solution Assembly** 
- **Current:** 3.3% complete solutions vs Claude's 50.0%
- **Issue:** Rarely finds single results with deprecation + replacement + authority
- **API Improvement:** Multi-result synthesis that combines authoritative deprecation notices with replacement guides, "solution chains" that link deprecated API docs to migration guides

**3. Deprecation Recency Intelligence**
- **Current:** Good authority (3.0) but missing some deprecation signals
- **Issue:** May surface older official docs that don't mention recent deprecations
- **API Improvement:** Temporal weighting for recently updated documentation, better understanding of version-specific deprecation language

### 💡 **Exa's Competitive Advantages (Keep These!)**
- **Authority scoring is excellent** (3.0 tier consistently)
- **Semantic understanding beats keyword search** (70% vs Google's 13.3% deprecation detection)  
- **Clean, structured results** vs Claude's hallucination risk

**The core insight:** Exa excels at finding authoritative content but needs better synthesis to deliver complete developer solutions. Claude wins by generating comprehensive answers, but Exa could win by intelligently combining authoritative sources.

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
  year={2025},
  note={Exa evaluation framework}
}
```
# Deprecation Search Evaluation Report

Generated: 2025-09-12 17:27:16
Evaluation ID: `20250912_172716`

## Overview

- **Total Queries**: 30
- **Systems Evaluated**: exa, google, stackoverflow, claude
- **Frameworks Covered**: nextjs, pytorch, tensorflow
- **Evaluation Period**: 20250912_172716

## Overall System Performance

### Summary Statistics

| System | Queries | Deprecation@k (mean) | Replacement Coverage (mean) | Authority@k (mean) | Time-to-Solution (success rate) |
|--------|---------|---------------------|-----------------------------|--------------------|----------------------------------|
| exa | 30 | 0.700 | 0.367 | 3.000 | 3.3% |
| google | 30 | 0.133 | 0.100 | 0.500 | 10.0% |
| stackoverflow | 30 | 0.000 | 0.000 | 1.000 | 0.0% |
| claude | 30 | 0.933 | 0.533 | 3.000 | 50.0% |

### Detailed Metrics


**Exa**
- Deprecation Detection: 70.0% success rate (mean: 0.700, median: 1.000)
- Replacement Coverage: 36.7% success rate (mean: 0.367, median: 0.000)
- Authority Level: Mean 3.00, Max 3 (median: 3.00)
- Time-to-Solution: 3.3% solved (1/30 queries, mean: 1.00, median: 1.00)

**Google**
- Deprecation Detection: 13.3% success rate (mean: 0.133, median: 0.000)
- Replacement Coverage: 10.0% success rate (mean: 0.100, median: 0.000)
- Authority Level: Mean 0.50, Max 3 (median: 0.00)
- Time-to-Solution: 10.0% solved (3/30 queries, mean: 1.67, median: 2.00)

**Stackoverflow**
- Deprecation Detection: 0.0% success rate (mean: 0.000, median: 0.000)
- Replacement Coverage: 0.0% success rate (mean: 0.000, median: 0.000)
- Authority Level: Mean 1.00, Max 1 (median: 1.00)
- Time-to-Solution: 0.0% solved (0/30 queries, mean: ∞, median: ∞)

**Claude**
- Deprecation Detection: 93.3% success rate (mean: 0.933, median: 1.000)
- Replacement Coverage: 53.3% success rate (mean: 0.533, median: 1.000)
- Authority Level: Mean 3.00, Max 3 (median: 3.00)
- Time-to-Solution: 50.0% solved (15/30 queries, mean: 1.00, median: 1.00)

## Per-Framework Analysis

### Nextjs Framework (40 queries)

| System | Queries | Deprecation@k | Replacement Coverage | Authority@k | TTS Success |
|--------|---------|---------------|---------------------|-------------|-------------|
| exa | 10 | 0.800 | 0.300 | 3.000 | 0.0% |
| google | 10 | 0.400 | 0.300 | 1.500 | 30.0% |
| stackoverflow | 10 | 0.000 | 0.000 | 1.000 | 0.0% |
| claude | 10 | 0.800 | 0.700 | 3.000 | 60.0% |

### Pytorch Framework (40 queries)

| System | Queries | Deprecation@k | Replacement Coverage | Authority@k | TTS Success |
|--------|---------|---------------|---------------------|-------------|-------------|
| exa | 10 | 0.400 | 0.200 | 3.000 | 10.0% |
| google | 10 | 0.000 | 0.000 | 0.000 | 0.0% |
| stackoverflow | 10 | 0.000 | 0.000 | 1.000 | 0.0% |
| claude | 10 | 1.000 | 0.600 | 3.000 | 60.0% |

### Tensorflow Framework (40 queries)

| System | Queries | Deprecation@k | Replacement Coverage | Authority@k | TTS Success |
|--------|---------|---------------|---------------------|-------------|-------------|
| exa | 10 | 0.900 | 0.600 | 3.000 | 0.0% |
| google | 10 | 0.000 | 0.000 | 0.000 | 0.0% |
| stackoverflow | 10 | 0.000 | 0.000 | 1.000 | 0.0% |
| claude | 10 | 1.000 | 0.300 | 3.000 | 30.0% |

## System Rankings

**Overall Effectiveness Ranking** (weighted average of all metrics):

1. **Claude** (score: 0.742)
   - Best at: deprecation detection, replacement coverage, high authority sources, complete solutions

2. **Exa** (score: 0.525)
   - Best at: deprecation detection, high authority sources

3. **Google** (score: 0.125)
   - Best at: consistent baseline performance

4. **Stackoverflow** (score: 0.083)
   - Best at: consistent baseline performance

## Methodology

This evaluation uses four key metrics:
1. **Deprecation@k**: Detection of deprecation language in top-k results
2. **Replacement Coverage**: Presence of replacement/migration guidance  
3. **Authority@k**: Maximum authority tier of sources (1=forums, 2=blogs, 3=official docs)
4. **Time-to-Solution**: Rank of first result meeting all criteria with authority ≥2

## Limitations

- **API Dependencies**: Some baselines limited by API quotas and availability
- **Authority Scoring**: Domain-specific sources may need manual curation for optimal scoring
- **Language Patterns**: Replacement coverage relies on heuristic patterns when ground truth labels unavailable
- **Query Coverage**: Current evaluation focuses primarily on nextjs, pytorch, tensorflow frameworks
- **Temporal Factors**: Deprecation information accuracy depends on recency of indexed content

## Future Work

- **Expanded Framework Coverage**: Add Python ML libraries (scikit-learn, pandas), mobile frameworks (React Native, Flutter)
- **Human Evaluation**: Incorporate expert assessment for result quality and relevance
- **Advanced Authority Scoring**: Machine learning-based authority classification using content features
- **Real-time Updates**: Integration with framework release cycles for timely deprecation detection
- **Multi-language Support**: Extend evaluation to non-English documentation and community content
- **Result Deduplication**: Implement semantic similarity filtering to reduce redundant results

---
*Report generated by eval_runner.py on 2025-09-12 at 17:27:16*  
*Evaluation ID: 20250912_172716*

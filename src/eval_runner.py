"""
Main evaluation runner for deprecation search baselines.

Loads queries, runs all baselines, computes metrics, and generates reports.
"""

import json
import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

from .exa_client import ExaClient
from .baselines.result import Result
from .baselines.google import GoogleBaseline
from .baselines.stackoverflow import StackOverflowBaseline  
from .baselines.claude import ClaudeBaseline
from .metrics import evaluate_baseline
from .utils import authority_score


class EvalRunner:
    """Main evaluation runner for deprecation search baselines."""
    
    def __init__(self):
        """Initialize the evaluation runner."""
        # Load environment variables
        load_dotenv()
        
        # Set up directories
        self.results_dir = Path("results")
        self.reports_dir = Path("reports")
        self.data_dir = Path("data")
        
        self.results_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        
        # Initialize clients
        self.exa_api_key = os.getenv("EXA_API_KEY")
        if not self.exa_api_key:
            print("Warning: EXA_API_KEY not found in environment")
            self.exa_client = None
        else:
            self.exa_client = ExaClient(self.exa_api_key)
        
        # Initialize baselines
        self.baselines = {}
        
        try:
            self.baselines["google"] = GoogleBaseline()
        except Exception as e:
            print(f"Warning: Google baseline initialization failed: {e}")
            
        try:
            self.baselines["stackoverflow"] = StackOverflowBaseline()
        except Exception as e:
            print(f"Warning: StackOverflow baseline initialization failed: {e}")
            
        try:
            self.baselines["claude"] = ClaudeBaseline()
        except Exception as e:
            print(f"Warning: Claude baseline initialization failed: {e}")
    
    def load_queries(self) -> List[Dict[str, Any]]:
        """Load queries from data/queries.jsonl."""
        queries_file = self.data_dir / "queries.jsonl"
        
        if not queries_file.exists():
            print(f"Warning: {queries_file} not found")
            return []
        
        queries = []
        try:
            with open(queries_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        query_data = json.loads(line)
                        queries.append(query_data)
            
            print(f"Loaded {len(queries)} queries from {queries_file}")
            return queries
            
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading queries: {e}")
            return []
    
    def load_labels(self) -> Dict[str, Dict[str, Any]]:
        """Load optional labels from data/labels.jsonl."""
        labels_file = self.data_dir / "labels.jsonl"
        
        if not labels_file.exists():
            print(f"Warning: {labels_file} not found - using heuristic replacements")
            return {}
        
        labels = {}
        try:
            with open(labels_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        label_data = json.loads(line)
                        query_id = label_data.get("id")
                        if query_id:
                            labels[query_id] = label_data
            
            print(f"Loaded {len(labels)} labels from {labels_file}")
            return labels
            
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading labels: {e}")
            return {}
    
    def convert_exa_to_results(self, exa_results: List[Dict[str, Any]]) -> List[Result]:
        """Convert Exa API results to Result objects."""
        results = []
        for exa_result in exa_results:
            url = exa_result.get("url", "")
            result = Result(
                title=exa_result.get("title", ""),
                url=url,
                snippet=exa_result.get("snippet", ""),
                score=None,  # Exa doesn't provide scores in this format
                authority_tier=authority_score(url)  # Set authority tier based on URL
            )
            results.append(result)
        return results
    
    def run_exa_baseline(self, query: str, k: int = 10) -> List[Result]:
        """Run Exa baseline for a query."""
        if not self.exa_client:
            return []
        
        try:
            exa_results = self.exa_client.search(query, k)
            return self.convert_exa_to_results(exa_results)
        except Exception as e:
            print(f"Error running Exa baseline for query '{query}': {e}")
            return []
    
    def run_all_systems(self, query_data: Dict[str, Any], k: int = 10) -> Dict[str, List[Result]]:
        """Run all available systems for a query."""
        query = query_data["query"]
        query_id = query_data.get("id", "unknown")
        
        results = {}
        
        # Run Exa baseline
        print(f"  Running Exa for {query_id}...")
        exa_results = self.run_exa_baseline(query, k)
        results["exa"] = exa_results
        
        # Run other baselines
        for system_name, baseline in self.baselines.items():
            print(f"  Running {system_name} for {query_id}...")
            try:
                system_results = baseline.run(query, k)
                results[system_name] = system_results
            except Exception as e:
                print(f"Error running {system_name} baseline: {e}")
                results[system_name] = []
        
        return results
    
    def evaluate_query(
        self, 
        query_data: Dict[str, Any], 
        labels: Dict[str, Dict[str, Any]], 
        k: int = 10
    ) -> Dict[str, Dict[str, float]]:
        """Evaluate all systems for a single query."""
        query_id = query_data.get("id", "unknown")
        
        # Get expected replacements from labels if available
        expected_replacements = None
        if query_id in labels:
            expected_replacements = labels[query_id].get("expected_replacements")
        
        # Run all systems
        all_results = self.run_all_systems(query_data, k)
        
        # Compute metrics for each system
        metrics_results = {}
        for system_name, results in all_results.items():
            if results:
                metrics = evaluate_baseline(results, expected_replacements, k)
                metrics_results[system_name] = metrics
            else:
                # Empty results - all metrics are 0
                metrics_results[system_name] = {
                    "deprecation_notice_at_k": 0.0,
                    "replacement_coverage": 0.0,
                    "authority_at_k": 0.0,
                    "time_to_solution": float('inf')
                }
        
        return metrics_results
    
    def run_evaluation(self, k: int = 10) -> Dict[str, Any]:
        """Run full evaluation across all queries and systems."""
        print("🚀 Starting deprecation search evaluation...")
        
        # Load data
        queries = self.load_queries()
        labels = self.load_labels()
        
        if not queries:
            print("❌ No queries found - cannot run evaluation")
            return {}
        
        # Track results across all queries
        all_results = []
        system_metrics = {}
        
        print(f"📊 Evaluating {len(queries)} queries with k={k}")
        
        # Process each query
        for i, query_data in enumerate(queries, 1):
            query_id = query_data.get("id", f"query_{i}")
            query = query_data.get("query", "")
            
            print(f"\n[{i}/{len(queries)}] Processing {query_id}: {query[:50]}...")
            
            # Evaluate query
            query_metrics = self.evaluate_query(query_data, labels, k)
            
            # Store results
            for system_name, metrics in query_metrics.items():
                result_row = {
                    "query_id": query_id,
                    "framework": query_data.get("framework", "unknown"),
                    "system": system_name,
                    **metrics
                }
                all_results.append(result_row)
                
                # Accumulate system metrics
                if system_name not in system_metrics:
                    system_metrics[system_name] = []
                system_metrics[system_name].append(metrics)
        
        return {
            "all_results": all_results,
            "system_metrics": system_metrics,
            "total_queries": len(queries)
        }
    
    def save_results(self, results: Dict[str, Any], timestamp: str) -> None:
        """Save results to parquet and CSV files."""
        if not results.get("all_results"):
            print("⚠️ No results to save")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(results["all_results"])
        
        # Save by system
        systems = df["system"].unique()
        for system in systems:
            system_df = df[df["system"] == system]
            
            # Save parquet
            parquet_file = self.results_dir / f"{system}_{timestamp}.parquet"
            system_df.to_parquet(parquet_file, index=False)
            
            # Save CSV  
            csv_file = self.results_dir / f"{system}_{timestamp}.csv"
            system_df.to_csv(csv_file, index=False)
            
            print(f"💾 Saved {system} results: {len(system_df)} rows")
    
    def _calculate_system_statistics(self, metrics_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate comprehensive statistics for a system's metrics."""
        if not metrics_list:
            return {}
        
        import statistics
        
        # Separate finite TTS values for better statistics
        finite_tts_values = [m["time_to_solution"] for m in metrics_list if m["time_to_solution"] != float('inf')]
        
        stats = {
            "queries_evaluated": len(metrics_list),
            "deprecation_notice_at_k": {
                "mean": statistics.mean(m["deprecation_notice_at_k"] for m in metrics_list),
                "median": statistics.median(m["deprecation_notice_at_k"] for m in metrics_list),
                "success_rate": sum(1 for m in metrics_list if m["deprecation_notice_at_k"] > 0) / len(metrics_list)
            },
            "replacement_coverage": {
                "mean": statistics.mean(m["replacement_coverage"] for m in metrics_list),
                "median": statistics.median(m["replacement_coverage"] for m in metrics_list),
                "success_rate": sum(1 for m in metrics_list if m["replacement_coverage"] > 0) / len(metrics_list)
            },
            "authority_at_k": {
                "mean": statistics.mean(m["authority_at_k"] for m in metrics_list),
                "median": statistics.median(m["authority_at_k"] for m in metrics_list),
                "max": max(m["authority_at_k"] for m in metrics_list)
            },
            "time_to_solution": {
                "finite_count": len(finite_tts_values),
                "success_rate": len(finite_tts_values) / len(metrics_list),
                "mean": statistics.mean(finite_tts_values) if finite_tts_values else float('inf'),
                "median": statistics.median(finite_tts_values) if finite_tts_values else float('inf')
            }
        }
        
        return stats
    
    def _aggregate_by_framework(self, all_results: List[Dict[str, Any]]) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """Aggregate results by framework and system."""
        framework_data = {}
        
        for result in all_results:
            framework = result.get("framework", "unknown")
            system = result["system"]
            
            if framework not in framework_data:
                framework_data[framework] = {}
            if system not in framework_data[framework]:
                framework_data[framework][system] = []
                
            framework_data[framework][system].append({
                "deprecation_notice_at_k": result["deprecation_notice_at_k"],
                "replacement_coverage": result["replacement_coverage"], 
                "authority_at_k": result["authority_at_k"],
                "time_to_solution": result["time_to_solution"]
            })
        
        return framework_data
    
    def generate_summary_report(self, results: Dict[str, Any], timestamp: str) -> None:
        """Generate comprehensive markdown summary report with real aggregated data."""
        if not results.get("system_metrics") or not results.get("all_results"):
            print("⚠️ No metrics to report")
            return
        
        report_file = self.reports_dir / "summary.md"
        
        # Calculate system-level statistics
        system_stats = {}
        for system_name, metrics_list in results["system_metrics"].items():
            if metrics_list:
                system_stats[system_name] = self._calculate_system_statistics(metrics_list)
        
        # Aggregate by framework
        framework_data = self._aggregate_by_framework(results["all_results"])
        
        # Start building the report
        report_content = f"""# Deprecation Search Evaluation Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Evaluation ID: `{timestamp}`

## Overview

- **Total Queries**: {results['total_queries']}
- **Systems Evaluated**: {', '.join(system_stats.keys()) if system_stats else 'None'}
- **Frameworks Covered**: {', '.join(framework_data.keys()) if framework_data else 'None'}
- **Evaluation Period**: {timestamp}

## Overall System Performance

### Summary Statistics

| System | Queries | Deprecation@k (mean) | Replacement Coverage (mean) | Authority@k (mean) | Time-to-Solution (success rate) |
|--------|---------|---------------------|-----------------------------|--------------------|----------------------------------|
"""
        
        for system_name, stats in system_stats.items():
            dep_mean = stats["deprecation_notice_at_k"]["mean"]
            rep_mean = stats["replacement_coverage"]["mean"]
            auth_mean = stats["authority_at_k"]["mean"]
            tts_success = stats["time_to_solution"]["success_rate"]
            queries = stats["queries_evaluated"]
            
            report_content += f"| {system_name} | {queries} | {dep_mean:.3f} | {rep_mean:.3f} | {auth_mean:.3f} | {tts_success:.1%} |\n"
        
        report_content += "\n### Detailed Metrics\n\n"
        
        for system_name, stats in system_stats.items():
            dep_stats = stats["deprecation_notice_at_k"]
            rep_stats = stats["replacement_coverage"]  
            auth_stats = stats["authority_at_k"]
            tts_stats = stats["time_to_solution"]
            
            tts_mean_str = f"{tts_stats['mean']:.2f}" if tts_stats['mean'] != float('inf') else "∞"
            tts_median_str = f"{tts_stats['median']:.2f}" if tts_stats['median'] != float('inf') else "∞"
            
            report_content += f"""
**{system_name.title()}**
- Deprecation Detection: {dep_stats['success_rate']:.1%} success rate (mean: {dep_stats['mean']:.3f}, median: {dep_stats['median']:.3f})
- Replacement Coverage: {rep_stats['success_rate']:.1%} success rate (mean: {rep_stats['mean']:.3f}, median: {rep_stats['median']:.3f})
- Authority Level: Mean {auth_stats['mean']:.2f}, Max {auth_stats['max']:.0f} (median: {auth_stats['median']:.2f})
- Time-to-Solution: {tts_stats['success_rate']:.1%} solved ({tts_stats['finite_count']}/{stats['queries_evaluated']} queries, mean: {tts_mean_str}, median: {tts_median_str})
"""
        
        # Per-Framework Breakdown
        report_content += "\n## Per-Framework Analysis\n\n"
        
        if framework_data:
            for framework, framework_systems in framework_data.items():
                framework_queries = sum(len(metrics) for metrics in framework_systems.values())
                report_content += f"### {framework.title()} Framework ({framework_queries} queries)\n\n"
                
                report_content += "| System | Queries | Deprecation@k | Replacement Coverage | Authority@k | TTS Success |\n"
                report_content += "|--------|---------|---------------|---------------------|-------------|-------------|\n"
                
                for system, metrics_list in framework_systems.items():
                    if metrics_list:
                        fw_stats = self._calculate_system_statistics(metrics_list)
                        dep_mean = fw_stats["deprecation_notice_at_k"]["mean"]
                        rep_mean = fw_stats["replacement_coverage"]["mean"]
                        auth_mean = fw_stats["authority_at_k"]["mean"]
                        tts_success = fw_stats["time_to_solution"]["success_rate"]
                        
                        report_content += f"| {system} | {len(metrics_list)} | {dep_mean:.3f} | {rep_mean:.3f} | {auth_mean:.3f} | {tts_success:.1%} |\n"
                
                report_content += "\n"
        else:
            report_content += "*No framework-specific data available*\n\n"
        
        # System Comparison Summary
        if len(system_stats) > 1:
            report_content += "## System Rankings\n\n"
            
            # Rank by overall effectiveness (combination of metrics)
            system_rankings = []
            for system_name, stats in system_stats.items():
                effectiveness_score = (
                    stats["deprecation_notice_at_k"]["mean"] * 0.25 +
                    stats["replacement_coverage"]["mean"] * 0.25 +
                    (stats["authority_at_k"]["mean"] / 3.0) * 0.25 +  # Normalize to 0-1
                    stats["time_to_solution"]["success_rate"] * 0.25
                )
                system_rankings.append((system_name, effectiveness_score, stats))
            
            system_rankings.sort(key=lambda x: x[1], reverse=True)
            
            report_content += "**Overall Effectiveness Ranking** (weighted average of all metrics):\n\n"
            for i, (system, score, stats) in enumerate(system_rankings, 1):
                report_content += f"{i}. **{system.title()}** (score: {score:.3f})\n"
                report_content += f"   - Best at: "
                
                best_metrics = []
                if stats["deprecation_notice_at_k"]["mean"] >= 0.5:
                    best_metrics.append("deprecation detection")
                if stats["replacement_coverage"]["mean"] >= 0.5:
                    best_metrics.append("replacement coverage")  
                if stats["authority_at_k"]["mean"] >= 2.5:
                    best_metrics.append("high authority sources")
                if stats["time_to_solution"]["success_rate"] >= 0.3:
                    best_metrics.append("complete solutions")
                
                report_content += ", ".join(best_metrics) if best_metrics else "consistent baseline performance"
                report_content += "\n\n"
        
        # Enhanced limitations and future work
        report_content += f"""## Methodology

This evaluation uses four key metrics:
1. **Deprecation@k**: Detection of deprecation language in top-k results
2. **Replacement Coverage**: Presence of replacement/migration guidance  
3. **Authority@k**: Maximum authority tier of sources (1=forums, 2=blogs, 3=official docs)
4. **Time-to-Solution**: Rank of first result meeting all criteria with authority ≥2

## Limitations

- **API Dependencies**: Some baselines limited by API quotas and availability
- **Authority Scoring**: Domain-specific sources may need manual curation for optimal scoring
- **Language Patterns**: Replacement coverage relies on heuristic patterns when ground truth labels unavailable
- **Query Coverage**: Current evaluation focuses primarily on {', '.join(framework_data.keys()) if framework_data else 'web development'} frameworks
- **Temporal Factors**: Deprecation information accuracy depends on recency of indexed content

## Future Work

- **Expanded Framework Coverage**: Add Python ML libraries (scikit-learn, pandas), mobile frameworks (React Native, Flutter)
- **Human Evaluation**: Incorporate expert assessment for result quality and relevance
- **Advanced Authority Scoring**: Machine learning-based authority classification using content features
- **Real-time Updates**: Integration with framework release cycles for timely deprecation detection
- **Multi-language Support**: Extend evaluation to non-English documentation and community content
- **Result Deduplication**: Implement semantic similarity filtering to reduce redundant results

---
*Report generated by eval_runner.py on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}*  
*Evaluation ID: {timestamp}*
"""
        
        # Write report
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"📄 Generated comprehensive summary report: {report_file}")
        print(f"   - {len(system_stats)} systems analyzed")
        print(f"   - {len(framework_data)} frameworks covered") 
        print(f"   - {results['total_queries']} total queries evaluated")


def main() -> None:
    """Main entry point for evaluation pipeline."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Initialize runner
    runner = EvalRunner()
    
    # Run evaluation
    results = runner.run_evaluation(k=10)
    
    if results:
        # Save results
        runner.save_results(results, timestamp)
        
        # Generate report
        runner.generate_summary_report(results, timestamp)
        
        print(f"\n✅ Evaluation complete! Check results/ and reports/ directories.")
    else:
        print("\n❌ Evaluation failed - no results generated")


if __name__ == "__main__":
    main()
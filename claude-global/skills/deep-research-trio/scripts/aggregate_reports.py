#!/usr/bin/env python3
"""
Aggregate and analyze Deep Research Trio reports.
Identifies consensus, divergence, and generates comparative analysis.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def load_latest_report(reports_dir: str) -> dict:
    """Load the most recent research report."""
    reports_path = Path(reports_dir)
    json_files = list(reports_path.glob("research-*.json"))

    if not json_files:
        raise FileNotFoundError(f"No research reports found in {reports_dir}")

    latest = max(json_files, key=lambda p: p.stat().st_mtime)
    print(f"Loading: {latest.name}")

    with open(latest) as f:
        return json.load(f)


def extract_key_points(text: str, max_points: int = 10) -> list[str]:
    """Extract key points from text (simple heuristic)."""
    if not text:
        return []

    # Split by common separators
    lines = text.replace('\n\n', '\n').split('\n')
    points = []

    for line in lines:
        line = line.strip()
        # Skip empty or very short lines
        if len(line) < 20:
            continue
        # Skip obvious headers
        if line.startswith('#') or line.endswith(':'):
            continue
        # Collect substantial lines
        if len(line) > 50:
            points.append(line[:300] + ('...' if len(line) > 300 else ''))

        if len(points) >= max_points:
            break

    return points


def find_consensus(results: list[dict]) -> list[str]:
    """Find points mentioned by 2+ platforms."""
    all_points = defaultdict(set)

    for result in results:
        if result.get('status') != 'success':
            continue

        platform = result.get('name', result.get('platform', 'unknown'))
        full_text = result.get('content', {}).get('fullText', '').lower()

        # Extract key terms/phrases
        words = full_text.split()
        for i in range(len(words) - 2):
            phrase = ' '.join(words[i:i+3])
            if len(phrase) > 15:  # Skip very short phrases
                all_points[phrase].add(platform)

    # Find phrases mentioned by multiple platforms
    consensus = [phrase for phrase, platforms in all_points.items()
                 if len(platforms) >= 2]

    return consensus[:20]  # Top 20


def find_unique_insights(results: list[dict]) -> dict[str, list[str]]:
    """Find insights unique to each platform."""
    unique = {}

    for result in results:
        if result.get('status') != 'success':
            continue

        platform = result.get('name', result.get('platform', 'unknown'))
        content = result.get('content', {})
        points = extract_key_points(content.get('fullText', ''))

        unique[platform] = points[:5]  # Top 5 unique points

    return unique


def compare_citations(results: list[dict]) -> dict:
    """Compare citations across platforms."""
    all_citations = defaultdict(set)
    platform_citations = {}

    for result in results:
        if result.get('status') != 'success':
            continue

        platform = result.get('name', result.get('platform', 'unknown'))
        citations = result.get('content', {}).get('citations', [])

        urls = set()
        for cite in citations:
            url = cite.get('url', '')
            if url:
                # Normalize URL
                domain = url.split('/')[2] if '/' in url else url
                urls.add(domain)
                all_citations[domain].add(platform)

        platform_citations[platform] = len(citations)

    # Find shared vs unique sources
    shared = [domain for domain, platforms in all_citations.items()
              if len(platforms) >= 2]
    unique_sources = {p: [] for p in platform_citations}

    for domain, platforms in all_citations.items():
        if len(platforms) == 1:
            platform = list(platforms)[0]
            unique_sources[platform].append(domain)

    return {
        'total_by_platform': platform_citations,
        'shared_sources': shared[:10],
        'unique_sources': {k: v[:5] for k, v in unique_sources.items()}
    }


def generate_aggregate_report(data: dict, output_path: str) -> str:
    """Generate comprehensive aggregate report."""
    query = data.get('query', 'Unknown query')
    results = data.get('results', [])
    summary = data.get('summary', {})

    # Analyze results
    unique_insights = find_unique_insights(results)
    citation_comparison = compare_citations(results)

    # Build report
    report = f"""# Deep Research Trio - Aggregate Analysis

## Query
> {query}

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Platforms | {summary.get('total', 0)} |
| Successful | {summary.get('success', 0)} |
| Partial/Timeout | {summary.get('partial', 0)} |
| Failed | {summary.get('failed', 0)} |
| Generated | {datetime.now().strftime('%Y-%m-%d %H:%M')} |

---

## Platform Comparison

| Platform | Status | Duration | Citations |
|----------|--------|----------|-----------|
"""

    for result in results:
        name = result.get('name', result.get('platform', 'Unknown'))
        status = result.get('status', 'unknown')
        duration = result.get('timing', {}).get('durationMinutes', '-')
        citations = len(result.get('content', {}).get('citations', []))

        status_emoji = '✅' if status == 'success' else '⚠️' if status in ['timeout', 'partial'] else '❌'
        report += f"| {name} | {status_emoji} {status} | {duration} min | {citations} |\n"

    report += """
---

## Citation Analysis

### Citation Count by Platform
"""

    for platform, count in citation_comparison['total_by_platform'].items():
        report += f"- **{platform}**: {count} citations\n"

    if citation_comparison['shared_sources']:
        report += """
### Shared Sources (2+ platforms)
"""
        for source in citation_comparison['shared_sources']:
            report += f"- {source}\n"

    report += """
---

## Key Points by Platform

"""

    for platform, points in unique_insights.items():
        report += f"### {platform}\n\n"
        for i, point in enumerate(points, 1):
            report += f"{i}. {point}\n\n"

    report += """
---

## Full Responses

"""

    for result in results:
        name = result.get('name', result.get('platform', 'Unknown'))
        content = result.get('content', {})
        full_text = content.get('fullText', '(No content)')

        report += f"""### {name}

<details>
<summary>Click to expand ({len(full_text)} characters)</summary>

{full_text}

</details>

---

"""

    # Save report
    with open(output_path, 'w') as f:
        f.write(report)

    return output_path


def main():
    """Main entry point."""
    reports_dir = os.path.join(os.path.dirname(__file__), '..', 'reports')

    # Check for specific file argument
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        if os.path.exists(input_file):
            with open(input_file) as f:
                data = json.load(f)
        else:
            print(f"File not found: {input_file}")
            sys.exit(1)
    else:
        data = load_latest_report(reports_dir)

    # Generate aggregate report
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    output_path = os.path.join(reports_dir, f'aggregate-{timestamp}.md')

    generate_aggregate_report(data, output_path)
    print(f"\n✅ Aggregate report generated: {output_path}")


if __name__ == '__main__':
    main()

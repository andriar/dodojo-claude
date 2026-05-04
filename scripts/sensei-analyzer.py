#!/usr/bin/env python3
"""
Sensei Pattern Analyzer
Mines telemetry + git + memory to generate optimization recommendations
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import sys

SENSEI_DIR = Path.home() / ".claude" / "sensei"
MEMORY_DIR = Path.home() / ".claude" / "memory"
PROJECT_DIR = Path.cwd()

class SenseiAnalyzer:
    def __init__(self):
        self.telemetry = []
        self.patterns = []
        self.file_reads = defaultdict(int)
        self.tool_usage = defaultdict(int)
        self.follow_up_chains = []
        self.memory_gaps = []

    def load_telemetry(self):
        """Load telemetry.jsonl from last 7 days"""
        telemetry_file = SENSEI_DIR / "telemetry.jsonl"
        if not telemetry_file.exists():
            return

        cutoff = datetime.now(tz=None) - timedelta(days=7)
        with open(telemetry_file) as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    ts_str = record['timestamp']
                    # Parse both formats: with and without timezone
                    if ts_str.endswith('Z'):
                        ts = datetime.fromisoformat(ts_str[:-1])  # Remove Z for naive parsing
                    else:
                        ts = datetime.fromisoformat(ts_str)
                    if ts >= cutoff:
                        self.telemetry.append(record)
                except Exception as e:
                    continue

    def analyze_repeated_reads(self):
        """Detect files read multiple times (should be memorized)"""
        file_reads = defaultdict(int)
        for record in self.telemetry:
            for file_access in record.get('files_accessed', []):
                path = file_access['path']
                file_reads[path] += file_access.get('reads', 1)

        for path, count in file_reads.items():
            if count >= 3:  # Read 3+ times
                # Assume substantial file if read multiple times
                tokens_per_read = 500  # Conservative estimate
                tokens_wasted = count * tokens_per_read
                self.patterns.append({
                    'rank': 0,  # Will sort later
                    'type': 'repeated-file-reads',
                    'severity': 'high' if count >= 5 else 'medium',
                    'file': path,
                    'reads_count': count,
                    'tokens_wasted': tokens_wasted,
                    'suggestion': f"Create memory file for '{path}' patterns. Use /dodojo:recall next time.",
                    'estimate_savings': f"{int(tokens_wasted/7)} tokens/week"
                })

    def analyze_follow_up_chains(self):
        """Detect prompts that needed clarification (inefficient)"""
        chains = []
        current_chain = []

        for record in self.telemetry:
            text = record['prompt']['text'].lower()
            # Heuristic: if prompt contains certain keywords, it's likely a follow-up
            is_followup = any(x in text for x in [
                'what do you mean', 'can you explain', 'like this', 'like that',
                'more specifically', 'can you clarify', 'what is', 'how do', 'why'
            ])

            if is_followup:
                current_chain.append(record)
            else:
                if len(current_chain) >= 2:
                    chains.append(current_chain)
                current_chain = [record]

        if chains:
            avg_chain = sum(len(c) for c in chains) / len(chains)
            if avg_chain > 2:
                total_wasted = len(chains) * int(avg_chain) * 1000  # Rough est
                self.patterns.append({
                    'rank': 0,
                    'type': 'follow-up-chain',
                    'severity': 'medium',
                    'avg_chain_length': round(avg_chain, 1),
                    'chains_count': len(chains),
                    'tokens_wasted': total_wasted,
                    'suggestion': 'Structure prompts: [goal]. Context: [X]. Format: [Y]. Examples: [Z]',
                    'estimate_savings': f"{int(total_wasted/7)} tokens/week"
                })

    def analyze_tool_misuse(self):
        """Detect when wrong tool was used"""
        for record in self.telemetry:
            tools = record.get('tools_used', [])
            for tool in tools:
                name = tool['name']
                # Read tool could be replaced by Bash + grep
                if name == 'Read':
                    text = record['prompt']['text'].lower()
                    if any(x in text for x in ['find', 'search', 'grep', 'where', 'which', 'location']):
                        self.patterns.append({
                            'rank': 0,
                            'type': 'tool-misuse',
                            'severity': 'low',
                            'tool_used': 'Read',
                            'alternative': 'Bash (grep)',
                            'suggestion': 'For text search: use `grep` or `awk` instead of reading full file',
                            'estimate_savings': '~100 tokens per search'
                        })
                        break  # One recommendation per analysis

    def analyze_memory_gaps(self):
        """Detect questions asked before but not answered in memory"""
        memory_files = set()
        if MEMORY_DIR.exists():
            for f in MEMORY_DIR.glob('**/*.md'):
                memory_files.add(f.name.lower())

        for record in self.telemetry:
            text = record['prompt']['text'].lower()
            if text.startswith(('how', 'what', 'can i', 'do i')):
                # This might be a common question
                # Check if similar memory exists
                # (Simple check - full version would use semantic search)
                keywords = text.split()[:3]
                matching_memory = [m for m in memory_files if any(k in m for k in keywords)]
                if not matching_memory and len(text) > 30:
                    self.patterns.append({
                        'rank': 0,
                        'type': 'memory-gap',
                        'severity': 'low',
                        'question': text[:60],
                        'suggestion': 'This question might be reusable. Create a memory file after answering.',
                        'estimate_savings': 'Avoid re-asking in future'
                    })
                    break  # One per analysis

    def _estimate_file_size(self, path):
        """Rough token estimate for file (1 token ~= 1 char)"""
        try:
            return len(Path(path).read_text())
        except:
            return 100  # Default

    def rank_patterns(self):
        """Sort patterns by severity + impact"""
        severity_order = {'high': 0, 'medium': 1, 'low': 2}
        self.patterns.sort(key=lambda x: (
            severity_order.get(x.get('severity', 'low'), 999),
            -x.get('tokens_wasted', 0)
        ))
        for i, p in enumerate(self.patterns):
            p['rank'] = i + 1

    def save_analysis(self):
        """Save analysis.json with recommendations"""
        output = {
            'generated_at': datetime.now().isoformat() + 'Z',
            'session_count': len(set(r.get('timestamp') for r in self.telemetry)),
            'total_tokens_7d': sum(
                r.get('response', {}).get('output', 0) + r.get('response', {}).get('input', 0)
                for r in self.telemetry
            ),
            'patterns': self.patterns[:5]  # Top 5 patterns
        }

        SENSEI_DIR.mkdir(parents=True, exist_ok=True)
        with open(SENSEI_DIR / 'analysis.json', 'w') as f:
            json.dump(output, f, indent=2)

        print(f"✅ Analysis saved: {SENSEI_DIR / 'analysis.json'}")
        return output

    def run(self):
        """Run full analysis"""
        self.load_telemetry()
        if not self.telemetry:
            print("No telemetry data available")
            return {}

        self.analyze_repeated_reads()
        self.analyze_follow_up_chains()
        self.analyze_tool_misuse()
        self.analyze_memory_gaps()
        self.rank_patterns()
        return self.save_analysis()


if __name__ == "__main__":
    analyzer = SenseiAnalyzer()
    analysis = analyzer.run()

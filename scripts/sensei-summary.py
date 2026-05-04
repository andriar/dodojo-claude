#!/usr/bin/env python3
"""
Sensei Summary - Display analysis in human-readable format
Shows top patterns + recommendations
"""

import json
from pathlib import Path
from datetime import datetime

SENSEI_DIR = Path.home() / ".claude" / "sensei"

def load_analysis():
    """Load latest analysis.json"""
    analysis_file = SENSEI_DIR / "analysis.json"
    if not analysis_file.exists():
        return None

    try:
        with open(analysis_file) as f:
            return json.load(f)
    except:
        return None

def format_analysis(analysis, count=1):
    """Format analysis for display (greeter: 1 pattern, full: 5)"""
    if not analysis or not analysis.get('patterns'):
        return None

    patterns = analysis['patterns'][:count]
    output = []

    output.append(f"🔍 SENSEI OPTIMIZATION (last {analysis.get('session_count', '?')} sessions)\n")

    for i, pattern in enumerate(patterns, 1):
        ptype = pattern.get('type', 'unknown')
        severity = pattern.get('severity', 'low')
        suggestion = pattern.get('suggestion', '')
        savings = pattern.get('estimate_savings', '')

        # Icon by severity
        icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(severity, '⚪')

        output.append(f"{icon} {ptype.replace('-', ' ').title()}")

        # Detail by type
        if ptype == 'repeated-file-reads':
            file = pattern.get('file', '?')
            reads = pattern.get('reads_count', 0)
            output.append(f"   File: {file} (read {reads}× this week)")
        elif ptype == 'follow-up-chain':
            avg = pattern.get('avg_chain_length', 0)
            output.append(f"   Clarification loops: {avg:.1f} prompts per task")
        elif ptype == 'tool-misuse':
            tool = pattern.get('tool_used', '?')
            alt = pattern.get('alternative', '?')
            output.append(f"   Using {tool} instead of {alt}")
        elif ptype == 'memory-gap':
            q = pattern.get('question', '?')
            output.append(f"   Question: {q}...")

        output.append(f"   → {suggestion}")
        output.append(f"   💰 {savings}\n")

    return "\n".join(output)

def show_greeter_summary():
    """Show 1 pattern in greeter (compact format)"""
    analysis = load_analysis()
    if not analysis or not analysis.get('patterns'):
        return

    pattern = analysis['patterns'][0]
    ptype = pattern.get('type', 'unknown')
    severity = pattern.get('severity', 'low')
    suggestion = pattern.get('suggestion', '')
    savings = pattern.get('estimate_savings', '')

    # Compact icon
    icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(severity, '⚪')

    # Single-line format for greeter
    title = ptype.replace('-', ' ').title()

    # Build compact output
    lines = []
    lines.append(f"\n{icon} SENSEI: {title}")

    # Detail based on type
    if ptype == 'repeated-file-reads':
        file = pattern.get('file', '?')
        reads = pattern.get('reads_count', 0)
        lines.append(f"   {file} read {reads}× this week")
    elif ptype == 'follow-up-chain':
        avg = pattern.get('avg_chain_length', 0)
        lines.append(f"   Clarification loops: {avg:.1f} prompts/task")
    elif ptype == 'tool-misuse':
        tool = pattern.get('tool_used', '?')
        alt = pattern.get('alternative', '?')
        lines.append(f"   Using {tool} vs {alt}")

    lines.append(f"   💡 {suggestion}")
    lines.append(f"   💰 {savings}\n")

    print("\n".join(lines))

def show_full_report():
    """Show all patterns + adoption tracking"""
    analysis = load_analysis()
    if not analysis:
        print("❌ No analysis available. Run a few sessions first.")
        return

    # Generate timestamp
    timestamp = analysis.get('generated_at', '?')

    print(f"\n{'='*60}")
    print(f"SENSEI OPTIMIZATION REPORT")
    print(f"{'='*60}\n")

    print(f"📊 Data: {analysis.get('session_count', 0)} sessions")
    print(f"📈 Total tokens used: {analysis.get('total_tokens_7d', 0):,}")
    print(f"🕐 Generated: {timestamp}\n")

    patterns = analysis.get('patterns', [])
    if not patterns:
        print("✅ No patterns detected. Your workflow is optimized!\n")
        return

    print(f"{'='*60}")
    print("RECOMMENDATIONS (ranked by impact)")
    print(f"{'='*60}\n")

    summary = format_analysis(analysis, count=len(patterns))
    print(summary)

    # Adoption tracking
    print(f"\n{'='*60}")
    print("HOW TO USE SENSEI")
    print(f"{'='*60}\n")
    print("1. Read the recommendation above")
    print("2. Try the suggested improvement")
    print("3. Run this report next week to see savings\n")

    # Estimate total savings
    total_savings = 0
    for p in patterns:
        wasted = p.get('tokens_wasted', 0)
        total_savings += wasted

    if total_savings > 0:
        print(f"💡 Potential savings if all adopted: ~{int(total_savings/7):,} tokens/week\n")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--full":
        show_full_report()
    else:
        show_greeter_summary()

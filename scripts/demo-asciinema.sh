#!/usr/bin/env bash
# Demo setup: prepare isolated environment to record DoDojo walkthrough

set -eu

DEMO_DIR="${DEMO_DIR:-.demo}"
DEMO_HOME="$DEMO_DIR/home"

echo "Setting up demo environment at $DEMO_DIR..."

# Create isolated home
mkdir -p "$DEMO_HOME/.claude"
cd "$DEMO_DIR"

# Simulate fresh install state
cat > "$DEMO_HOME/.bashrc" <<'EOF'
export HOME="$HOME"
export PATH="/usr/local/bin:/usr/bin:/bin"
PS1="\$ "
alias claude="echo 'Claude Code CLI (simulated)'"
EOF

# Pre-populate memory with realistic git history
mkdir -p "$DEMO_HOME/.claude/sessions"
cat > "$DEMO_HOME/.claude/sessions/sample.jsonl" <<'EOF'
{"date":"2026-05-01","task":"docs","commits":5}
{"date":"2026-05-02","task":"refactor","commits":3}
{"date":"2026-05-03","task":"bugfix","commits":2}
{"date":"2026-05-04","task":"feature","commits":8}
EOF

echo "✓ Demo environment ready at $DEMO_DIR"
echo ""
echo "To record asciinema:"
echo "  HOME=$DEMO_HOME asciinema rec docs/demo.cast --title 'DoDojo Quickstart' --cols 80 --rows 24"
echo ""
echo "Demo flow (45 sec):"
echo "  1. (5s)  Show: /dodojo:status"
echo "  2. (10s) Show: /dodojo:sensei (pattern mining)"
echo "  3. (10s) Show: greeter banner (memory, context, route, buddy)"
echo "  4. (15s) Explain: next steps (routing, memory, audit)"
echo "  5. (5s)  Show: /dodojo:init --help (setup is one command)"
echo ""

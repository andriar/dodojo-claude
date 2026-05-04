# Troubleshooting Guide

> Common issues + solutions

## Installation & Setup

### Plugin won't install

**Error:** `Command not found: /plugin`

**Solution:**
- Make sure you're in Claude Code (not terminal)
- Type `/plugin` in Claude Code prompt
- If still fails: restart Claude Code completely

**Error:** `marketplace add` fails

**Solution:**
```bash
# Try manual install
git clone https://github.com/andriar/dodojo-claude ~/.claude/plugins/manual/dodojo
/plugin install dodojo
```

### Settings.json errors

**Error:** Hooks not running

**Solution:**
```bash
# Check hook health
/dodojo:health

# If hooks failed:
# 1. Verify hook files exist:
ls -la ~/.claude/hooks/dodojo-*.sh

# 2. Check they're executable:
chmod +x ~/.claude/hooks/*.sh

# 3. Verify registered in settings.json:
cat ~/.claude/settings.json | grep "hooks"
```

---

## Memory & Storage

### Memory files not loading

**Symptom:** `/dodojo:recall` finds nothing

**Solution:**
1. Check memory directory exists:
   ```bash
   ls -la ~/.claude/memory/
   ```

2. Check files have proper frontmatter:
   ```bash
   head ~/.claude/memory/my-memory.md
   # Should start with:
   # ---
   # name: ...
   # ---
   ```

3. Verify metadata fields:
   ```bash
   # Should have:
   name, description, type, category
   ```

### Memory injection not working

**Symptom:** Memories exist but not injected into prompts

**Solution:**
1. Check smart-context hook registered:
   ```bash
   /dodojo:health
   ```

2. Try manual injection:
   ```bash
   /dodojo:recall "search term"
   ```

3. Check memory files are readable:
   ```bash
   chmod 644 ~/.claude/memory/**/*.md
   ```

### Memory getting too large

**Symptom:** System slow, context injection slow

**Solution:**
```bash
# Check memory health
python3 ~/.claude/scripts/orphan-detector.py

# Archive stale memories (dry-run first)
python3 ~/.claude/scripts/orphan-detector.py --archive

# Archive with confirmation
python3 ~/.claude/scripts/orphan-detector.py --archive --commit

# Check what was archived
cat ~/.claude/memory/_archive/manifest.json
```

### Restore archived memory

**Solution:**
```bash
# Find in archive
ls ~/.claude/memory/_archive/

# Move back
mv ~/.claude/memory/_archive/filename.md ~/.claude/memory/

# Update manifest manually if needed
```

---

## Sensei

### Sensei not showing recommendations

**Symptom:** Greeter shows "No Sensei data available"

**Solution:**
1. Run sessions first (need telemetry data):
   - Sensei needs 5+ prompts to detect patterns
   - Wait a few sessions

2. Check Sensei files exist:
   ```bash
   ls -la ~/.claude/sensei/
   # Should have: telemetry.jsonl, analysis.json
   ```

3. Force analyzer run:
   ```bash
   python3 ~/.claude/scripts/sensei-analyzer.py
   cat ~/.claude/sensei/analysis.json
   ```

### Sensei recommendations seem wrong

**Symptom:** Suggests something you already do

**Solution:**
- Sensei is learning from limited data (early sessions)
- Give it more sessions to improve
- Recommendations improve over time

### Sensei report missing

**Error:** `python3 ~/.claude/scripts/sensei-report` not found

**Solution:**
```bash
# Use full path
python3 ~/.claude/scripts/sensei-summary.py --full
```

---

## Smart Tips

### Tips not showing in greeter

**Symptom:** No daily tip appearing

**Solution:**
1. Check tips file exists:
   ```bash
   cat data/tips.json | head
   ```

2. Check tips-display hook registered:
   ```bash
   /dodojo:health
   ```

3. Test tips manually:
   ```bash
   python3 ~/.claude/scripts/tips-selector.py general
   ```

### Tips feedback not tracked

**Symptom:** Click [👍 helpful] but doesn't count

**Solution:**
```bash
# Log feedback manually
python3 ~/.claude/scripts/tips-selector.py --feedback tip_id_001 👍

# Check feedback file
cat ~/.claude/dodojo/tips-feedback.jsonl
```

---

## Orphan Detection

### Orphan detector slow

**Symptom:** `orphan-detector.py` takes >5 seconds

**Solution:**
- First run parses all memories (slow)
- Subsequent runs faster (cached)
- Normal for >100 memories

### Won't archive memories

**Error:** `--commit` flag not working

**Solution:**
```bash
# Make sure directory writable
chmod 755 ~/.claude/memory/

# Try again
python3 ~/.claude/scripts/orphan-detector.py --archive --commit
```

### Accidentally archived important memory

**Solution:**
```bash
# Restore from archive
mv ~/.claude/memory/_archive/filename.md ~/.claude/memory/

# Verify it's back
ls ~/.claude/memory/ | grep filename
```

---

## Performance

### Claude Code slow on startup

**Symptom:** Greeter takes 10+ seconds

**Solution:**
1. Check how many memories exist:
   ```bash
   find ~/.claude/memory/ -name "*.md" | wc -l
   ```

2. If >500: archive stale ones
   ```bash
   python3 ~/.claude/scripts/orphan-detector.py --archive --commit
   ```

3. Disable greeter temporarily (test mode):
   ```bash
   # In settings.json, set:
   "KAGAMI_SILENT": "1"
   ```

### Tokens wasted on memory injection

**Symptom:** Smart-context injecting irrelevant memories

**Solution:**
1. Check memory metadata (reuses, category):
   ```bash
   head -20 ~/.claude/memory/category/file.md
   ```

2. Update metadata if missing:
   ```yaml
   ---
   name: Proper Name
   category: frontend  # Important!
   ---
   ```

3. Run orphan detection to remove low-reuse files:
   ```bash
   python3 ~/.claude/scripts/orphan-detector.py --archive --commit
   ```

---

## Getting Help

**Check these first:**
1. [FEATURES.md](FEATURES.md) — what each feature does
2. [mental-model.md](guides/mental-model.md) — why DoDojo exists
3. Run `/dodojo:health` — smoke-test all hooks

**Still stuck?**
1. Open an issue: https://github.com/andriar/dodojo-claude/issues
2. Include:
   - What you tried
   - Error message (if any)
   - Output of `/dodojo:health`
   - Output of `/dodojo:status`

---

## Advanced Debugging

### Check hook execution

```bash
# Run specific hook manually
bash ~/.claude/hooks/sensei-greeter.sh

# Check stderr
bash ~/.claude/hooks/sensei-greeter.sh 2>&1
```

### Check script logs

```bash
# Sensei analyzer
python3 ~/.claude/scripts/sensei-analyzer.py -v

# Orphan detector verbose
python3 ~/.claude/scripts/orphan-detector.py --verbose
```

### Reset to defaults

```bash
# Backup current config
cp ~/.claude/settings.json ~/.claude/settings.json.bak

# Rerun setup
/dodojo:init --reset
```

### Check memory file syntax

```bash
# Validate YAML frontmatter
python3 -c "import yaml; yaml.safe_load(open('~/.claude/memory/file.md'))"
```

---

## Still Not Working?

1. **Check logs:** `~/.claude/dodojo/logs/` (if exists)
2. **Restart Claude Code:** Often fixes transient issues
3. **File an issue:** Include output from `/dodojo:health`

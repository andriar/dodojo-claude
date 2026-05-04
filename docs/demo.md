# Demo — screencast walkthrough

Watch DoDojo in action. 60-second asciinema showing install → greeter → Sensei recommendation.

## Watch it

Play the recording:

```bash
asciinema play docs/demo.cast
```

Or view online: [asciinema.org/a/...](https://asciinema.org/a/) (link TBD after first recording).

## What you'll see

- **Greeter banner** — Memory health, context matches, route (haiku/sonnet/opus suggestion), Buddy XP counter
- **Sensei pattern** — "You repeated this 40× this week—consider automating it"
- **One-command setup** — `/dodojo:init` walks through config in 90 seconds
- **Next ROI** — What to automate first (by impact, not code smell)

Emphasis: **quiet workflow discipline, no magic**. Just mines your own patterns.

## Record it yourself

Prerequisite: `asciinema` installed.

```bash
# 1. Set up demo environment
bash scripts/demo-asciinema.sh

# 2. Record (opens fresh terminal)
HOME=.demo/home asciinema rec docs/demo.cast \
  --title "DoDojo — Quiet Workflow Discipline" \
  --cols 80 --rows 24

# 3. (In asciinema) Follow demo flow below
# 4. (Press Ctrl-D to stop recording)

# 5. Verify
asciinema play docs/demo.cast
```

### Demo flow (45 sec talk-through)

**Setup (5 sec)**
```bash
# Show fresh state
/dodojo:status
# Output: greeter banner with memory, context, route, buddy stats
```

**Pattern mining (10 sec)**
```bash
# Show what Sensei found
/dodojo:sensei
# Output: Weekly report with 3–5 automation ideas ranked by ROI
# Example: "Repeated 'git add . && git commit' 47× → save 20 min/week"
```

**Greeter in action (10 sec)**
- Scroll back to show greeter from session start
- Highlight: memory health (✓), context injection (3 matches), route suggestion (haiku), buddy XP

**Setup wizard (15 sec)**
```bash
/dodojo:init
# Walk through theme/icons/Coach prompts (show defaults)
# Takes ~90 sec, writes to ~/.claude/settings.json
```

**Closeout (5 sec)**
- Show: "Next: read docs/quickstart.md"
- Mention: "First rec arrives in 7 days, or run /dodojo:sensei now"

### Tips for recording

- **Speed**: Use asciinema's playback speed (2x) to trim silence. Record at normal pace, play back faster.
- **Timing**: Command output doesn't auto-advance. Pause briefly after each command finishes before typing next.
- **Mistakes**: Re-record or cut/splice. (asciinema is JSON under the hood; editable.)
- **Audio**: No voice. Let UX speak. Add narration in YouTube/blog post if sharing.

## Using the demo

- **README hero**: Link in main README as "See it in action"
- **Blog/showcase**: Embed on landing page
- **Docs**: Link from quickstart ("Watch the 60-second version first")

## Maintenance

- **Refresh**: Re-record if UI changes (greeter, wizard questions, Sensei format)
- **Retention**: Keep in repo. asciinema.org can delete old recordings. Source of truth is `docs/demo.cast`
- **Playback**: Works offline. No external dependencies (unlike YouTube)

# PR Review Patterns — Weekly Analysis

Analyze this week's GitHub/GitLab PR review comments and identify recurring patterns.

## Step 1 — Fetch raw data

Run the fetch script:

```
python3 fetch.py
```

This writes `output/comments.json` with all review comments from the past 7 days
across every repo configured in `config.py` (GitHub and/or GitLab).
If it fails, report the error and stop.

## Step 2 — Group by pattern

Read `output/comments.json` and analyze the comments. For each comment, infer:

- **Category**: what type of issue does it raise? (e.g. naming, error handling, performance, types, formatting, security, test coverage, architecture, writing style, UX copy, conventions)
- **Codebase area**: which directory or module is the file in? (derive from `path`)
- **Automation tier** — classify each pattern into exactly one:
  - `linter` — can be caught statically (ESLint rule, Stylelint, custom AST rule)
  - `agent-rule` — can't be a linter, but can be a CLAUDE.md instruction (style conventions, naming patterns, UX copy guidelines, language/register choices, architecture preferences)
  - `template` — belongs in a PR template, issue template, or checklist
  - `human` — requires judgment; not automatable

Cluster semantically similar comments together. Two comments about the same issue worded differently count as one pattern.

When comments come from multiple platforms (field `platform`: github / gitlab), note that in the report — cross-platform patterns are especially strong signals.

## Step 3 — Build the report

Write `output/YYYY-WW.md` (use the ISO week of today's date). Structure:

```markdown
# PR Review Patterns — Week YYYY-WW

**Period:** YYYY-MM-DD to YYYY-MM-DD  
**PRs/MRs analyzed:** N  
**Total comments:** N  
**Unique patterns found:** N

---

## Top Patterns

### 1. [Pattern name] — N comments (X%)

**Category:** [category]  
**Codebase areas:** [list of directories/modules]  
**Platforms:** [github / gitlab / both]  
**Automation tier:** [linter / agent-rule / template / human]  
**Example comment:**
> "[verbatim quote from a real comment]"

**Suggested action:** [one concrete sentence]

---

[repeat for each pattern with ≥2 occurrences, ordered by frequency]

---

## Single-occurrence comments

[Brief bullet list of one-off issues — no deep analysis needed]

---

## Signal summary

| Pattern | Count | % | Platform | Tier |
|---------|-------|---|----------|------|
| ...     | ...   | ...| ...     | ...  |

---

## Proposed agent rules (CLAUDE.md)

For every pattern with tier `agent-rule`, write the exact instruction text ready to paste
into a CLAUDE.md file. Be specific and actionable — write the rule as it should appear,
not a description of it.

### [Pattern name]

```
[Exact CLAUDE.md instruction text, written as a direct rule.
Example: "Write all UI copy using 'vos' (not 'tú'). Argentina and Latin America
are the target markets. Use 'vos tenés', 'vos podés', never 'tú tienes'."]
```

[repeat for each agent-rule pattern]

---

## Recommended next actions

1. [Highest-impact linter rule to add]
2. [Highest-impact CLAUDE.md rule to add]
3. [Any template or process change]
```

## Step 4 — Offer to apply agent rules

After writing the report, ask the user:

> "Found N patterns that could become CLAUDE.md rules. Do you want me to add any of them?
> If yes, tell me which ones and the path to the CLAUDE.md file."

If the user confirms, append the approved rules under a `## Code review patterns` section
in the target CLAUDE.md. Create the section if it doesn't exist; don't duplicate rules
that are already there (check by semantic similarity, not exact string match).

## Step 5 — Print a summary to chat

Output to chat:

- Total comments and PRs/MRs analyzed
- Top 3 patterns with their percentages and automation tier
- How many are linter candidates vs agent-rule candidates
- Path to the full report

Keep the chat output under 20 lines.

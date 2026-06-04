# Pre-mortem Red Team

## What it does

Pre-mortem Red Team stress-tests a plan before the user commits to it.

The skill assumes the plan failed 12 months later, works backward to plausible causes, attacks the plan's load-bearing assumptions, ranks failure modes by likelihood and impact, and pairs the top risks with monitoring thresholds and mitigation packages.

The goal is not to be pessimistic. The goal is to make the plan harder to break.

The skill is pure method by default. If a failure mode depends on an external fact, the agent may optionally use the Decision-Grade Research search adapter to gather source candidates for that assumption.

## When to use it

- The user has a concrete plan, launch, strategy, decision, or proposal.
- The user wants to know why it might fail before investing more time or money.
- The user needs leading indicators and mitigation moves, not just a generic risk list.
- The plan has assumptions that should be made explicit and attacked.
- A high-risk assumption needs a lightweight external evidence check.

Do not use it for executing the plan, vague brainstorming without a plan, or final licensed legal, financial, or medical advice.

## Example input

```text
We plan to launch a fictional AI note-taking app for independent consultants in Q3. The plan is to sell annual subscriptions through LinkedIn content and founder-led demos. Stress-test the plan before we build the launch calendar.
```

## Expected output

- Plan summary and decision context
- Ranked failure modes scored by likelihood and impact
- The load-bearing assumption each failure mode breaks
- Early-warning indicator and monitoring threshold for each top failure mode
- Mitigation package per top failure mode
- Residual risks the user should accept knowingly
- Optional source-candidate notes for fact-sensitive assumptions
- Date-named local output files under `skills/premortem-redteam/output/`, such as `2026-06-04-premortem-report.html`

## Safety / boundaries

- Keep the stance adversarial but constructive.
- Attack assumptions and causal logic, not people.
- Use fictional examples in public materials.
- Do not hard-code search API keys or commit raw private search output.
- Do not present this as final legal, financial, medical, or investment advice.
- `output/` contents are local run artifacts and should not be published.

---
name: openspec-parent-workflow
description: Apply parent branch, commit, and review rules during an explicitly activated OpenSpec implementation session.
disable-model-invocation: true
---

# OpenSpec parent workflow

## Activation and scope

Only an explicit user activation starts this workflow. Use `/skill:openspec-parent-workflow <change-id>` before `/opsx-apply <change-id>`.
A local OpenSpec directory, existing proposal, or worker selection does not activate it.
Do not activate it for exploration, proposal creation, ordinary coding, or an unrelated fix.

These rules apply only to the main agent that owns the selected OpenSpec implementation change.
Delegated agents follow their assigned tasks. They do not activate the parent workflow independently.
A reference to a milestone means a task group.

## Active workflow

After explicit activation, read `references/openspec-workflow.md` relative to this skill directory.
That reference defines task groups, local branch stacks, per-task commits, the 2,500-line review trigger, review requests, and result handling.
Resolve the selected change and its tasks through the normal OpenSpec apply instructions before implementation.
Read `worker-selection` before selecting `worker` or `smart-worker`.
Do not push, fetch, create hosted PRs, or merge branches. The user publishes the complete branch stack manually.

## Completion and exit

The workflow ends when the selected change completes, the user cancels it, or the user explicitly switches to ordinary work.
A paused change does not make unrelated work part of this workflow.
After exit, do not apply its branch, commit, or automatic-review rules to later ordinary tasks.
Preserve existing commits and unfinished work. A different OpenSpec change needs fresh explicit activation.

Skills add instructions to conversation history, not an enforced runtime mode.
Use `/reload` after skill or global-instruction changes. Use `/new` when a clean ordinary-work session is necessary.

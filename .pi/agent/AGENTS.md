# Pi workstream guidance

Read the `worker-selection` skill before selecting `worker` or `smart-worker`, and when starting an OpenSpec implementation workstream, including apply.

For a parent-owned OpenSpec implementation workstream, read `references/openspec-workflow.md` relative to the worker-selection skill directory. It defines task groups, local branch stacks, per-task commits, the 2,500-line review trigger, review requests, and result handling.

A reference to a milestone means a task group.

Delegated agents follow their assigned tasks. They do not start the parent branch and review workflow independently. These triggers do not authorize implementation during explore mode or proposal creation.

Project instructions or explicit user instructions can skip automatic reviews. Record `review_skipped`, preserve local branch rules, and do not claim approval.

No agent pushes, fetches, creates hosted PRs, or merges branches. The user publishes the complete branch stack manually.

# OpenSpec parent workflow

These instructions apply only to the main agent in an explicitly activated `openspec-parent-workflow` session.
The parent owns the selected OpenSpec implementation change. Delegated agents follow their task assignments.
After completion, cancellation, or an explicit return to ordinary work, do not apply this workflow to later tasks.
Read the selection skill before choosing workers.

## Resolve the change and tasks

- Follow the installed OpenSpec apply workflow and its user authorization. Do not implement during exploration or proposal creation.
- Resolve the change, artifact paths, and scope from OpenSpec status and apply instructions. Preserve any selected `--store` flag on later OpenSpec commands.
- A task group is a top-level numbered heading in the resolved task file, such as `## 2. Group title` with tasks `2.1`, `2.2`.
- If no numbered groups exist, treat the whole task list as task group 1.
- Review is an automatic workflow step. Do not add review-gate checkboxes to the task plan.

## Local branch stack

Use the user's target base, or local `main` or `master` by default. Do not fetch or change the base branch. Stop if the working tree contains unrelated changes that prevent a safe branch operation.

- Create the initial task-group branch `<change-id>-<n>` from the target base for the first group, or from the latest completed branch afterward.
- Continue the same task group on `<change-id>-<n>-<m>`, with the continuation number starting at 2.
- Use `git switch -c` for new branches. Do not replace an existing branch or discard work when a name already exists.
- Leave completed branches unchanged. Only the current branch gets implementation changes or accepted review fixes.
- Commit each task's explicit paths after its checks pass. Include its task ID in the commit message and preserve unrelated changes.
- Track the branch's task IDs and its immediate base. The review covers that branch's committed changes, not the whole stack again.

## Size trigger and review entry

After each implementation task commit, measure reviewable additions plus deletions against the immediate base.
Replace the placeholders with shell-quoted values from the resolved repository and immediate base.
Execute the assignments as separate commands before Python, all in one Bash call. Do not use command-prefix assignments.

```bash
REPO='<repository>'
BASE='<base>'
python /home/gerrit/dotfiles/.pi/agent/agents/code-review/preflight.py --repo "${REPO:?repository is required}" --base "${BASE:?base is required}"
```

Use `changed_lines` only from a successful result. The helper applies the same exclusions as the reviewer. Empty filtered input counts as zero lines. Size has no preflight limit.

- Below 2,500 lines with tasks remaining, continue on the same branch.
- At 2,500 or more lines with tasks remaining, pause implementation and request review of the completed branch tasks.
- Request review at group completion even below 2,500 lines.
- Do not estimate line counts during planning. One task can cross the threshold, so the threshold is a trigger rather than a final diff cap.
- Pass the applicable task checks with the review request. Report missing checks rather than inventing successful verification.

If project instructions or the user explicitly skip reviews, do not call the coordinator. Record the parent-only status `review_skipped` and follow the same size-trigger and branch rules. This status does not claim approval.

## Review request

Start a fresh `pr-review-orchestrator` run for each branch. Use a descriptive unique name, such as `review-group-2-part-2`. Supply:

- `repository`: canonical repository path.
- `change_id`: selected OpenSpec change.
- `task_group`: number and title.
- `branch_tasks`: task IDs implemented on this branch.
- `deferred_tasks`: remaining tasks on later branches or groups.
- `branch`: current branch name.
- `base`: immediate local target branch name.
- `expected_head`: current committed code SHA.
- `artifact_paths`: resolved files for proposal, design, tasks, and capability specs. These can be local or ignored by Git.
- `verification`: checks completed, results, and checks that could not run.

The coordinator owns its one-time preflight and review-repair loop. Await automatic subagent result delivery. Do not poll, inspect session logs for completion, or edit the checkout while the coordinator works.

## Handle the result

- `review_approved`: verify repository, change, task group, branch, base name, and `reviewed_head` against the current committed target after any review fixes.
- `not_reviewed`: accept this expected outcome when exclusions leave no input. Record it without claiming that code review occurred.
- `review_skipped`: record the explicit opt-out. This is a parent status, not a coordinator output.
- `blocked` or `failed`: report the reason and stop progression. Do not create the next branch or execute further tasks.
- If the result reports a confirmed defect already present in the base, pause and report it before any further work, even with current-branch approval.

After an accepted outcome with tasks remaining, create the next continuation branch from the completed branch. After group completion, create the next task-group branch from the completed branch. Do not create an extra branch when the whole change is complete.

On a new parent session, discover existing branches by name and ancestry and check the task file. Re-review the latest branch whose assigned tasks are complete before creating its successor. Project or user opt-out still applies. Do not recreate existing branches or infer approval from a branch name alone.

## Final report and authority

Report the ordered stack with branch, base, task group, task IDs, outcome, and reviewed code SHA for each branch. Keep `not_reviewed` and `review_skipped` explicit. Report unresolved inherited defects and skipped checks separately.

The parent creates local branches and commits implementation tasks. The coordinator stages and commits accepted fixes only. No agent pushes, fetches, creates hosted PRs, merges branches, resets, or removes unrelated work. The user publishes the stack manually after implementation.

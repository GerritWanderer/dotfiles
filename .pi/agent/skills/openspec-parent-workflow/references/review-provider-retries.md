# Review-agent provider retries

## Scope

Apply this policy only at these delegated review-agent boundaries:

| Caller | Agent |
| --- | --- |
| OpenSpec parent | `pr-review-orchestrator` |
| Review coordinator | `pr-agent-reviewer` |

This reference does not activate the OpenSpec parent workflow.
It does not authorize worker retries, ordinary-task retries, or another PR-Agent CLI command.
Keep the CLI's existing internal retry and fallback policy unchanged.

## Record one logical invocation

Before dispatch, keep the complete request and source-state snapshot in the caller's session.
After the tool identifies its actual model, record the resolved provider, model, and thinking level.
Do not substitute the current profile defaults for a failed invocation's resolved model.

Keep these fields in the caller's private invocation record:

- `logical_invocation_id`: stable identity for the original request and its retry.
- `agent`: one of the two review agents above.
- `resolved_provider`, `resolved_model`, and `resolved_thinking`: actual tool identities, including caller overrides.
- `workflow_retry_count`: zero before the first attempt, one after the caller consumes the only retry allowance.
- `request_snapshot`: repository, change, task group, task IDs, branch, base, expected commit, artifact paths, exclusions, and verification inputs.
- `source_snapshot`: canonical repository, branch, base name and commit, expected commit, and tracked and untracked source state.
- `run_context`: available findings, rejected requests, repair history, entry snapshot, and generated output paths.

A resumed or replacement session keeps the same invocation identity and consumed allowance.
Do not create another allowance merely because the child name or session changes.
Tool-internal retries are separate from this workflow allowance.
The same logical invocation has at most two workflow attempts: the original and one extra attempt.
Missing invocation history stops automatic retry rather than resetting the counter.

## Classify the failure

First distinguish a returned review outcome from an agent invocation failure.
Returned `blocked` or `failed` review outcomes keep their existing handling. Do not reinterpret them as provider failures to restart the review.
The earlier invocation must stop before a retry starts.

A retry candidate needs explicit evidence that the delegated agent's own model-provider request failed temporarily.
The qualifying provider HTTP statuses are `408`, `429`, `500`, `502`, `503`, and `504`.
Explicit provider transport timeouts and connection resets also qualify.
An unexplained timeout or a failed local command does not qualify.

Permanent causes override a qualifying status code.
Do not retry automatically for any of these causes:

- Invalid credentials, permissions, provider configuration, or model identity.
- Explicit quota exhaustion, including a permanent quota error with HTTP 429.
- Missing session files, terminal delivery failures, a closed pane, cancellation, or an interrupted agent.
- Preflight failures, missing or unknown coverage, code findings, failed tests, or unsuccessful repairs.
- PR-Agent CLI failures after its configured internal policy.
- Unknown failure origin or ambiguous evidence.

Report only the provider status and a safe error category. Remove credentials from evidence and do not copy raw secret-bearing error text.

## Check state and preserve the request

Compare the current canonical repository, branch, base name and commit, expected commit, and source state with the dispatch snapshot.
New commits, source edits, or unrelated untracked files stop automatic retry.
Generated artifacts at the known approved output paths do not count as source edits.
Preserve necessary earlier output evidence before an authorized overwrite. A stale output file is not current review evidence.

Keep the original task scope, artifact paths, exclusions, verification inputs, and rejection reasons.
If planning inputs changed and the caller cannot recover the original context, stop and report the missing context.
Do not reset repair history, failed-fix escalation, or current review admission checks.
Do not discard partial edits to make a retry eligible.

The retry must use the same resolved provider, model, and thinking level.
Keep caller model overrides. Unknown identity or an unsupported original model stops automatic retry.
A replacement profile with a different thinking level needs an explicit caller decision.

## Execute one retry

When all checks pass and `workflow_retry_count` is zero, consume the allowance before dispatch.
Set `workflow_retry_count` to one and retry automatically without another user approval request.
Do not start a polling loop, retry timer, or repeated status check.

Prefer the same addressable session when it retains the necessary request and run context.
If that session is unavailable, start one replacement only when the complete necessary context and original model identity are available.
Pass the original resolved model explicitly and verify the replacement's reported provider, model, and thinking level.
A changed identity stops the replacement rather than authorizing another attempt.

A resumed coordinator keeps its entry snapshot and does not repeat full preflight in the same repair run.
A genuinely new coordinator run executes its normal one-time entry preflight.
These state checks do not replace preflight or alter the shared exclusions.

If the extra attempt also fails, stop and report both attempts. Another attempt needs an explicit user decision.
If the retry returns `blocked` or `failed`, keep that outcome and stop normal progression.
A child failure result does not authorize an outer whole-run restart or a new child retry allowance.

## Evidence and outcomes

Record the role, resolved model, safe provider error category, attempt count, state checks, and final result in verification evidence.
Keep the existing public review outcome schema.
Successful invocation recovery alone does not approve the review.
Coverage, target checks, tests, findings, and inherited-defect handling remain necessary before task progression.
A retry that returns unknown coverage stays blocked. Do not add a third attempt or weaken the coverage checks.

## Decision examples

| Case | Result |
| --- | --- |
| Coordinator invocation ends with provider HTTP 503, unchanged state, and unused allowance | Retry once with the same resolved model |
| Reviewer invocation ends with provider HTTP 503, unchanged state, and unused allowance | Retry once with the same resolved model |
| Worker invocation ends with provider HTTP 503 | No retry under this review-only policy |
| Caller model override differs from the profile default | Preserve the override during the retry |
| Provider HTTP 429 explicitly reports quota exhaustion | Stop, even with an unused allowance |
| Authentication or configuration failure | Stop and report the permanent cause |
| Source state, base commit, or review target changes | Stop and report the changed state |
| Necessary model or repair history is unavailable | Stop rather than guessing or resetting history |
| Generated review artifacts change at approved paths, but source state does not | Preserve evidence and retain retry eligibility |
| First attempt fails with HTTP 503, and the extra attempt also fails | Stop after two attempts |
| Session changes after the allowance is consumed | Keep the consumed allowance and stop another automatic attempt |
| Returned review outcome is blocked through unknown coverage | Report the blocker without another attempt |
| Retry returns usable review evidence | Apply normal review checks without claiming approval from the retry alone |

Contract tests check these written rules. Controlled acceptance cases check caller dispatch behavior separately.
Do not claim runtime acceptance from text assertions or a simulated decision function alone.

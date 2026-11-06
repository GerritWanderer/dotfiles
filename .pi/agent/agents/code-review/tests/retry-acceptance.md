# Controlled review-provider retry acceptance

## Purpose and boundaries

Exercise caller decisions with controlled review-agent tool results, without forcing a live provider failure.
Run the cases for both callers: an OpenSpec parent with `pr-review-orchestrator`, and a coordinator with `pr-agent-reviewer`.
Do not invoke workers, repair source, change provider settings, or use live CLI failures as retry triggers.
This checklist does not activate the OpenSpec parent workflow.

Profile contract tests verify the written policy and links. They do not verify actual agent dispatch.
A simulated decision function alone does not complete this acceptance checklist.
Record actual caller dispatches, their model and request fields, final outcomes, and any unchecked role.

## Fixture setup

1. Load the shared `review-provider-retries.md` reference as test context.
2. Give the caller a known logical invocation, complete request, resolved model override, thinking level, source snapshot, and necessary run history.
3. Supply a stopped review-agent invocation with a controlled failure or result.
4. Capture every dispatch after that result independently. Do not let the fixture decide whether the caller retries.
5. Compare the dispatch count and copied request with the expected case.
6. Record the tested caller and whether the endpoint was simulated or live.

Use original model identity `github-copilot/gpt-6.1-sol` with thinking level `high` as an override fixture.
The profile default can differ. The retry must preserve this fixture's resolved identity.
Keep `workflow_retry_count` zero initially unless the case specifies a consumed allowance.

## Cases

The dispatch count below includes the original controlled invocation.

| ID | Controlled result or changed state | Expected caller behavior |
| --- | --- | --- |
| `provider-503` | Own provider HTTP 503, stopped invocation, unchanged state | Two dispatches, with the original model, thinking level, and request |
| `provider-statuses` | Repeat with provider HTTP 408, 429, 500, 502, and 504 | At most two dispatches per logical invocation |
| `provider-transport` | Explicit provider transport timeout or connection reset | Two dispatches when all other guards pass |
| `model-override` | Profile default differs from the fixture override | Two dispatches with the fixture override, not the profile default |
| `retry-exhausted` | Original invocation and extra attempt both fail with HTTP 503 | Two dispatches, then stop and report both attempts |
| `session-replaced` | Session changes after `workflow_retry_count` becomes one | No third dispatch and no counter reset |
| `quota-exhausted` | HTTP 429 explicitly reports permanent quota exhaustion | One dispatch, then report the permanent cause |
| `authentication` | Invalid credentials or permissions | One dispatch and no automatic retry |
| `configuration` | Invalid configuration or unsupported model | One dispatch and no automatic retry |
| `worker-excluded` | Worker invocation has provider HTTP 503 | One dispatch under this review-only policy |
| `unknown-origin` | Timeout or error without explicit provider origin | One dispatch and no automatic retry |
| `interrupted` | Pane closure, cancellation, missing session, or delivery failure | One dispatch and no automatic retry |
| `still-active` | The earlier invocation remains active | No concurrent extra dispatch |
| `source-changed` | Source state or unrelated untracked files differ | One dispatch and a changed-state report |
| `target-changed` | Branch, base name, base commit, or expected commit differs | One dispatch and a target-mismatch report |
| `model-unknown` | Original resolved model or thinking level is unknown | One dispatch and no guessed model |
| `history-missing` | Necessary repair, rejection, or invocation history is unavailable | One dispatch and no allowance reset |
| `outputs-only` | Only approved generated review artifacts change | Preserve evidence, then allow the extra dispatch with unchanged source |
| `returned-failure` | Reviewer returns a structured `failed` review outcome | One dispatch and normal failed-outcome handling |
| `cli-failure` | PR-Agent CLI fails after its internal policy | No extra CLI command or workflow retry |
| `coverage-blocked` | Extra attempt returns blocked through unknown JSON coverage | Two dispatches, no third attempt, and no task progression |
| `recovery` | Extra attempt returns a usable review result | Two dispatches, then apply normal review and target checks |

## Evidence record

For each case, record the caller, fixture result, logical invocation ID, dispatch count, resolved identity, request comparison, source checks, and final outcome.
Report status codes and safe categories rather than secret-bearing raw errors.
Distinguish successful invocation recovery from review approval.
Leave a case or caller unchecked when actual dispatch evidence is unavailable.

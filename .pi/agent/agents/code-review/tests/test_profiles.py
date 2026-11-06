"""Check the agent profiles and shared workflow references."""

import os
from pathlib import Path
import re
import shlex
import subprocess
import unittest


AGENT_DIR = Path(__file__).resolve().parents[3]


def profile(name):
    text = (AGENT_DIR / "agents" / f"{name}.md").read_text()
    _, frontmatter, body = text.split("---", 2)
    fields = dict(line.split(":", 1) for line in frontmatter.strip().splitlines())
    return {key: value.strip() for key, value in fields.items()}, body.strip()


class ProfileContractTests(unittest.TestCase):
    def test_worker_contracts_match(self):
        worker, worker_body = profile("worker")
        smart, smart_body = profile("smart-worker")
        self.assertEqual(worker_body, smart_body)
        self.assertEqual(worker["model"], "github-copilot/gpt-6.1-terra")
        self.assertEqual(smart["model"], "github-copilot/gpt-6.1-sol")
        for key in ("tools", "subagent_agents", "thinking", "system-prompt", "auto-exit"):
            self.assertEqual(worker[key], smart[key])
        self.assertEqual(worker["subagent_agents"], "scout, researcher")
        self.assertIn("ask_question", worker_body)
        self.assertIn("unrelated failures", worker_body)
        self.assertNotIn("Stop searching after three", worker_body)
        self.assertNotIn("Self-review checklist", worker_body)

    def test_review_profiles_load_shared_selection(self):
        for name in ("pr-agent-reviewer", "pr-review-orchestrator"):
            with self.subTest(name=name):
                fields, body = profile(name)
                self.assertEqual(fields["skills"], "worker-selection")
                self.assertNotIn("| Score", body)
                self.assertNotIn("milestone", body.lower())
                self.assertNotRegex(body, r"pr_agent_(milestone_runs|branch_runs|followup_used)")

    def test_reviewer_preserves_model_and_read_only_tools(self):
        fields, body = profile("pr-agent-reviewer")
        self.assertEqual(fields["model"], "github-copilot/gpt-6-sol")
        self.assertEqual(fields["thinking"], "medium")
        self.assertEqual(fields["tools"], "read, grep, find, ls, bash")
        self.assertNotIn("preflight.py", body)
        self.assertIn("filter_source.overrides", body)
        self.assertIn("artifact_paths", body)
        self.assertIn("expected_head", body)
        self.assertIn("--pr_reviewer.enable_review_coverage_footer=true", body)
        self.assertIn("--pr_code_suggestions.enable_suggestions_coverage_footer=true", body)

    def test_reviewer_places_guarded_json_option_before_review(self):
        _, body = profile("pr-agent-reviewer")
        command = re.search(r"```bash\n(.*?)\n```", body, re.S).group(1)
        base = "feature/review-base"
        output = "/tmp/review repo's $literal/review.md.json"
        setup = (
            f"BASE={shlex.quote(base)}\nREVIEW_JSON={shlex.quote(output)}\n"
            "COMMON_ARGS=('--ignore.glob=[]' '--config.propagate_tool_errors=true')\n"
            "REVIEW_INSTRUCTIONS='review scope'\n"
            "pr-agent() { printf '%s\\0' \"$@\"; }\n"
        )
        env = dict(os.environ)
        env.pop("BASH_ENV", None)
        result = subprocess.run(
            ["bash", "--noprofile", "--norc", "-c", setup + command],
            env=env, text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.stdout.split("\0")[:-1], [
            "--pr_url", base, "--json-output", output, "review",
            "--ignore.glob=[]", "--config.propagate_tool_errors=true",
            "--pr_reviewer.enable_review_coverage_footer=true",
            "--pr_reviewer.extra_instructions=review scope",
        ])

    def test_reviewer_blocks_empty_base_or_json_output(self):
        _, body = profile("pr-agent-reviewer")
        command = re.search(r"```bash\n(.*?)\n```", body, re.S).group(1)
        for missing in ("BASE", "REVIEW_JSON"):
            with self.subTest(missing=missing):
                values = {"BASE": "main", "REVIEW_JSON": "/tmp/review.md.json"}
                values[missing] = ""
                setup = "\n".join(f"{key}={shlex.quote(value)}" for key, value in values.items())
                setup += "\nCOMMON_ARGS=()\nREVIEW_INSTRUCTIONS='scope'\n"
                setup += "pr-agent() { printf 'UNEXPECTED_COMMAND'; }\n"
                env = dict(os.environ)
                env.pop("BASH_ENV", None)
                result = subprocess.run(
                    ["bash", "--noprofile", "--norc", "-c", setup + command],
                    env=env, text=True, capture_output=True, check=False,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertIn("is required", result.stderr)

    def test_structured_coverage_keeps_failure_checks(self):
        _, reviewer = profile("pr-agent-reviewer")
        for token in (
            "output_paths.review_json", "coverage.files_not_reviewed",
            "coverage.files_partially_reviewed", "arrays of strings",
            "Do not replace missing fields with empty arrays.",
            "Failed or incomplete chunks block complete coverage",
            "Missing, invalid, or stale JSON", "final full-diff packing",
            "A missing warning footer alone is not a blocker.",
        ):
            self.assertIn(token, reviewer)
        _, coordinator = profile("pr-review-orchestrator")
        for token in (
            "output_paths.review_json", "all four resolved output paths",
            "Missing, invalid, or stale JSON", "failed or incomplete chunks remain blockers",
            "Empty coverage arrays alone do not prove complete coverage.",
        ):
            self.assertIn(token, coordinator)

    def test_coordinator_owns_entry_check_and_local_repairs(self):
        fields, body = profile("pr-review-orchestrator")
        self.assertEqual(fields["model"], "github-copilot/gpt-6.1-terra")
        self.assertEqual(fields["thinking"], "high")
        self.assertEqual(fields["subagent_agents"], "pr-agent-reviewer, worker, smart-worker")
        self.assertEqual(body.count("preflight.py"), 1)
        self.assertIn("filter_source.overrides", body)
        self.assertIn("Do not repeat the entry check", body)
        self.assertIn("one fresh review", body)
        self.assertIn("not_reviewed", body)
        self.assertIn("never closes", body)
        self.assertIn("initial failed fix", body)
        self.assertIn("If it returns `blocked`, return `blocked` with its reason", body)
        self.assertIn("Partial or unknown", (AGENT_DIR / "agents" / "pr-agent-reviewer.md").read_text())

    def test_entry_examples_assign_values_before_argument_expansion(self):
        _, coordinator = profile("pr-review-orchestrator")
        reference = (
            AGENT_DIR / "skills" / "openspec-parent-workflow" / "references" / "openspec-workflow.md"
        ).read_text()
        repository = "/tmp/review repo's $literal"
        base = "feature/review-base"
        script = str(AGENT_DIR / "agents" / "code-review" / "preflight.py")
        for source, body in (("coordinator", coordinator), ("parent", reference)):
            with self.subTest(source=source):
                example = re.search(r"```bash\n(.*?)\n```", body, re.S)
                self.assertIsNotNone(example, "The entry example must use one Bash block.")
                command = example.group(1).replace("'<repository>'", shlex.quote(repository))
                command = command.replace("'<base>'", shlex.quote(base))
                for inherited in (None, {"REPO": "stale repository", "BASE": "stale-base"}):
                    with self.subTest(inherited=inherited):
                        env = dict(os.environ)
                        for key in ("REPO", "BASE", "BASH_ENV"):
                            env.pop(key, None)
                        env.update(inherited or {})
                        capture = "python() { printf '%s\\0' \"$@\"; }\n"
                        result = subprocess.run(
                            ["bash", "--noprofile", "--norc", "-c", capture + command],
                            env=env, text=True, capture_output=True, check=False,
                        )
                        self.assertEqual(result.returncode, 0, result.stderr)
                        self.assertEqual(result.stderr, "")
                        self.assertEqual(
                            result.stdout.split("\0")[:-1],
                            [script, "--repo", repository, "--base", base],
                        )

    def test_public_result_schema_matches_contract(self):
        _, body = profile("pr-review-orchestrator")
        schema = re.search(r"```yaml\n(.*?)\n```", body, re.S).group(1)
        fields = dict(line.split(":", 1) for line in schema.splitlines())
        expected = {
            "review_outcome", "repository", "branch", "base", "change_id", "task_group",
            "branch_tasks", "reviewed_head", "planning_context", "cli_coverage", "review_cycles",
            "fix_commits", "earlier_branch_defects", "summary", "remaining_findings", "verification",
            "blocker", "next_action", "hosted_pr_approval",
        }
        self.assertEqual(set(fields), expected)
        self.assertEqual(fields["review_outcome"].strip(), "review_approved | not_reviewed | blocked | failed")
        self.assertNotIn("review_skipped", schema)
        self.assertNotIn("base_head", schema)

    def test_worker_selection_does_not_activate_openspec_workflow(self):
        directory = AGENT_DIR / "skills" / "worker-selection"
        text = (directory / "SKILL.md").read_text()
        self.assertIn("name: worker-selection", text)
        for score in range(1, 6):
            self.assertIn(f"| {score} |", text)
        self.assertFalse((directory / "references" / "openspec-workflow.md").exists())
        self.assertNotIn("starting an OpenSpec implementation workstream", text)
        self.assertIn("This skill selects workers only.", text)
        self.assertIn("does not activate branch stacks", text)
        self.assertIn("formal score report", text)
        self.assertIn("Missing requirements need clarification", text)

    def test_global_instructions_do_not_activate_openspec_workflow(self):
        text = (AGENT_DIR / "AGENTS.md").read_text()
        self.assertIn("worker-selection", text)
        self.assertIn("explicit-only `openspec-parent-workflow`", text)
        self.assertIn("Do not apply those rules to ordinary coding", text)
        self.assertIn("existing proposal does not activate", text)
        self.assertNotIn("starting an OpenSpec implementation workstream", text)
        self.assertNotIn("references/openspec-workflow.md", text)
        self.assertNotIn("review_skipped", text)
        self.assertNotIn("A reference to a milestone means a task group.", text)

    def test_openspec_parent_skill_is_explicit_and_scoped(self):
        directory = AGENT_DIR / "skills" / "openspec-parent-workflow"
        text = (directory / "SKILL.md").read_text()
        _, frontmatter, body = text.split("---", 2)
        fields = dict(line.split(":", 1) for line in frontmatter.strip().splitlines())
        self.assertEqual(fields["name"].strip(), "openspec-parent-workflow")
        self.assertEqual(fields["disable-model-invocation"].strip(), "true")
        self.assertIn("Only an explicit user activation starts this workflow.", body)
        self.assertIn("/skill:openspec-parent-workflow <change-id>", body)
        self.assertIn("before `/opsx-apply <change-id>`", body)
        self.assertIn("existing proposal, or worker selection does not activate", body)
        self.assertIn("main agent", body)
        self.assertIn("Delegated agents follow their assigned tasks", body)
        self.assertIn("A reference to a milestone means a task group.", body)
        self.assertIn("the user explicitly switches to ordinary work", body)
        self.assertIn("A different OpenSpec change needs fresh explicit activation.", body)
        self.assertIn("references/openspec-workflow.md", body)
        self.assertTrue((directory / "references" / "openspec-workflow.md").is_file())

    def test_retry_policy_limits_roles_and_provider_errors(self):
        directory = AGENT_DIR / "skills" / "openspec-parent-workflow" / "references"
        text = (directory / "review-provider-retries.md").read_text()
        self.assertIn("| OpenSpec parent | `pr-review-orchestrator` |", text)
        self.assertIn("| Review coordinator | `pr-agent-reviewer` |", text)
        self.assertIn("does not authorize worker retries", text)
        self.assertIn("does not activate the OpenSpec parent workflow", text)
        statuses = set(re.findall(r"`(408|429|500|502|503|504)`", text))
        self.assertEqual(statuses, {"408", "429", "500", "502", "503", "504"})
        for token in (
            "Permanent causes override a qualifying status code.",
            "Explicit quota exhaustion", "Invalid credentials", "Missing session files",
            "PR-Agent CLI failures", "Unknown failure origin", "earlier invocation must stop",
            "Returned `blocked` or `failed` review outcomes keep their existing handling.",
        ):
            self.assertIn(token, text)

    def test_retry_policy_preserves_identity_budget_and_state(self):
        directory = AGENT_DIR / "skills" / "openspec-parent-workflow" / "references"
        text = (directory / "review-provider-retries.md").read_text()
        for token in (
            "logical_invocation_id", "workflow_retry_count", "request_snapshot",
            "source_snapshot", "run_context", "resolved_provider", "resolved_model",
            "resolved_thinking", "same resolved provider, model, and thinking level",
            "at most two workflow attempts", "consume the allowance before dispatch",
            "Do not create another allowance", "Missing invocation history stops automatic retry",
            "New commits, source edits, or unrelated untracked files stop automatic retry.",
            "Do not reset repair history", "Do not discard partial edits",
            "Another attempt needs an explicit user decision.",
            "A child failure result does not authorize an outer whole-run restart",
            "A retry that returns unknown coverage stays blocked.",
        ):
            self.assertIn(token, text)

    def test_retry_callers_load_shared_policy_without_global_trigger(self):
        directory = AGENT_DIR / "skills" / "openspec-parent-workflow" / "references"
        parent = (directory / "openspec-workflow.md").read_text()
        _, coordinator = profile("pr-review-orchestrator")
        self.assertIn("Before dispatch, read `review-provider-retries.md`", parent)
        self.assertIn("Retry once automatically with the same resolved model", parent)
        self.assertIn("Returned review outcomes, preflight blockers, and unknown coverage never qualify", parent)
        self.assertIn("openspec-parent-workflow/references/review-provider-retries.md", coordinator)
        self.assertIn("Retry once automatically with the same resolved model", coordinator)
        self.assertIn("Do not reset findings, rejection reasons, repair history", coordinator)
        self.assertIn("Returned `blocked` or `failed` review outcomes do not qualify.", coordinator)
        self.assertIn("After the extra attempt fails, return `failed` and stop.", coordinator)
        self.assertNotIn("review-provider-retries.md", (AGENT_DIR / "AGENTS.md").read_text())
        self.assertNotIn("review-provider-retries.md", (AGENT_DIR / "skills" / "worker-selection" / "SKILL.md").read_text())

    def test_retry_acceptance_checklist_separates_runtime_evidence(self):
        text = (AGENT_DIR / "agents" / "code-review" / "tests" / "retry-acceptance.md").read_text()
        cases = set(re.findall(r"^\| `([^`]+)` \|", text, re.M))
        self.assertEqual(cases, {
            "provider-503", "provider-statuses", "provider-transport", "model-override",
            "retry-exhausted", "session-replaced", "quota-exhausted", "authentication",
            "configuration", "worker-excluded", "unknown-origin", "interrupted", "still-active",
            "source-changed", "target-changed", "model-unknown", "history-missing",
            "outputs-only", "returned-failure", "cli-failure", "coverage-blocked", "recovery",
        })
        self.assertIn("OpenSpec parent with `pr-review-orchestrator`", text)
        self.assertIn("coordinator with `pr-agent-reviewer`", text)
        self.assertIn("They do not verify actual agent dispatch.", text)
        self.assertIn("Do not let the fixture decide whether the caller retries.", text)
        self.assertIn("Leave a case or caller unchecked when actual dispatch evidence is unavailable.", text)

    def test_caller_reference_covers_workflow_outcomes(self):
        text = (AGENT_DIR / "skills" / "openspec-parent-workflow" / "references" / "openspec-workflow.md").read_text()
        for token in (
            "<change-id>-<n>", "<change-id>-<n>-<m>", "2,500", "review_approved", "not_reviewed",
            "review_skipped", "blocked", "failed", "artifact_paths", "expected_head", "deferred_tasks",
            "Do not add review-gate checkboxes", "Re-review", "manually",
        ):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()

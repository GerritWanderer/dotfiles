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
            AGENT_DIR / "skills" / "worker-selection" / "references" / "openspec-workflow.md"
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

    def test_shared_selection_table_and_reference(self):
        directory = AGENT_DIR / "skills" / "worker-selection"
        text = (directory / "SKILL.md").read_text()
        self.assertIn("name: worker-selection", text)
        for score in range(1, 6):
            self.assertIn(f"| {score} |", text)
        self.assertTrue((directory / "references" / "openspec-workflow.md").is_file())
        self.assertIn("formal score report", text)
        self.assertIn("Missing requirements need clarification", text)

    def test_global_instructions_keep_parent_and_worker_roles_separate(self):
        text = (AGENT_DIR / "AGENTS.md").read_text()
        self.assertIn("A reference to a milestone means a task group.", text)
        self.assertIn("parent-owned", text)
        self.assertIn("Delegated agents follow their assigned tasks", text)
        self.assertIn("review_skipped", text)
        self.assertIn("manually", text)

    def test_caller_reference_covers_workflow_outcomes(self):
        text = (AGENT_DIR / "skills" / "worker-selection" / "references" / "openspec-workflow.md").read_text()
        for token in (
            "<change-id>-<n>", "<change-id>-<n>-<m>", "2,500", "review_approved", "not_reviewed",
            "review_skipped", "blocked", "failed", "artifact_paths", "expected_head", "deferred_tasks",
            "Do not add review-gate checkboxes", "Re-review", "manually",
        ):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()

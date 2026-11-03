"""Use temporary repositories. Do not run the PR-Agent CLI or models."""

import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.dont_write_bytecode = True
SCRIPT = Path(__file__).resolve().parents[1] / "preflight.py"
spec = importlib.util.spec_from_file_location("preflight", SCRIPT)
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)

KEYS = {
    "ok", "reason", "message", "repo", "branch", "base", "head", "base_head",
    "merge_base", "commits", "changed_files", "reviewable_files", "changed_lines",
    "max_changed_lines", "excluded_files", "output_paths", "filter_source",
}


class Repository:
    def __init__(self, root):
        self.path = Path(root) / "repo"
        self.path.mkdir()
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Offline Test")
        self.git("config", "user.email", "offline@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "core.hooksPath", str(Path(root) / "no-hooks"))
        self.write("seed.txt", "base\n")
        self.commit("base")
        self.git("switch", "-c", "feature")

    def git(self, *args):
        env = os.environ.copy()
        env["GIT_OPTIONAL_LOCKS"] = "0"
        proc = subprocess.run(
            ["git", "-C", str(self.path), *args], env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        if proc.returncode:
            raise AssertionError(proc.stderr.decode("utf-8", "replace"))
        return proc.stdout

    def write(self, path, data):
        target = self.path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data.encode("utf-8") if isinstance(data, str) else data)

    def commit(self, message="feature"):
        self.git("add", "--all")
        self.git("commit", "-m", message)

    def feature(self, count=2):
        self.write("feature.py", "".join(f"line_{i}\n" for i in range(count)))
        self.commit()

    def snapshot(self):
        index = self.path / ".git/index"
        files = {}
        for path in self.path.rglob("*"):
            if ".git" in path.relative_to(self.path).parts:
                continue
            if path.is_symlink():
                files[str(path.relative_to(self.path))] = ("link", os.readlink(path))
            elif path.is_file():
                files[str(path.relative_to(self.path))] = ("file", hashlib.sha256(path.read_bytes()).hexdigest())
        return index.read_bytes(), self.git("ls-files", "--stage", "-z"), self.git("rev-parse", "HEAD^{tree}"), self.git("show-ref"), files


class MockProbe:
    def __init__(self, repo, paths=None, exclusions=None):
        self.repo = repo
        self.paths = paths or {
            "review": str(repo.path / "review.md"),
            "improve": str(repo.path / "improve.md"),
            "describe": str(repo.path / "description.md"),
        }
        self.exclusions = exclusions or {}

    def __call__(self, repo, base=None, files=None, head=None, base_head=None):
        result = {"output_paths": self.paths.copy(), "filter_source": {"mock": "Git text patches"}, "files": []}
        if base is None:
            return result
        merge_base = self.repo.git("merge-base", base_head, head).decode().strip()
        for row in files:
            path = row["path"]
            if path in self.exclusions:
                result["files"].append({"path": path, "reason": self.exclusions[path]})
                continue
            patch = self.repo.git(
                "diff", "--no-ext-diff", "--no-textconv", "--no-color", "--find-renames",
                merge_base, head, "--", row["old_path"], path,
            ).decode("utf-8")
            result["files"].append({"path": path, "patch": patch})
        return result


class RepoTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="preflight-")
        self.addCleanup(self.temp.cleanup)
        self.repo = Repository(self.temp.name)

    def run_check(self, *, base=None, probe=None, path=None, expected=0, reason="ok"):
        args = ["--repo", str(path or self.repo.path)]
        if base is not None:
            args += ["--base", base]
        stream = io.StringIO()
        before = self.repo.snapshot()
        with mock.patch.object(preflight, "package_probe", probe or MockProbe(self.repo)):
            with contextlib.redirect_stdout(stream):
                code = preflight.main(args)
        text = stream.getvalue()
        result, end = json.JSONDecoder().raw_decode(text)
        self.assertEqual(text[end:], "\n")
        self.assertIsInstance(result, dict)
        self.assertEqual(set(result), KEYS)
        self.assertEqual(code, expected, result)
        self.assertEqual(result["reason"], reason, result)
        self.assertEqual(result["ok"], code == 0)
        self.assertEqual(result["max_changed_lines"], 2000)
        self.assertEqual(before, self.repo.snapshot())
        return result


class PreflightTests(RepoTestCase):
    def test_clean_small_feature_and_canonical_repo(self):
        self.repo.feature()
        (self.repo.path / "nested").mkdir()
        alias = Path(self.temp.name) / "alias"
        alias.symlink_to(self.repo.path / "nested", target_is_directory=True)
        result = self.run_check(path=alias)
        self.assertEqual(result["repo"], str(self.repo.path.resolve()))
        self.assertEqual(result["branch"], "feature")
        self.assertEqual(result["base"], "main")
        self.assertEqual(result["commits"], 1)
        self.assertEqual(result["changed_files"], 1)
        self.assertEqual(result["reviewable_files"], ["feature.py"])
        self.assertEqual(result["changed_lines"], 2)
        self.assertIn("not a token guarantee", result["message"])

    def test_2000_passes(self):
        self.repo.feature(2000)
        self.assertEqual(self.run_check()["changed_lines"], 2000)

    def test_2001_blocks(self):
        self.repo.feature(2001)
        result = self.run_check(expected=1, reason="changed_line_limit_exceeded")
        self.assertEqual(result["changed_lines"], 2001)

    def test_additions_and_deletions_both_count(self):
        self.repo.write("source.py", "old\n" * 1000)
        self.repo.commit("old source")
        self.repo.git("branch", "-f", "main", "HEAD")
        self.repo.write("source.py", "new\n" * 1000)
        self.repo.commit()
        self.assertEqual(self.run_check()["changed_lines"], 2000)

    def test_staged_unstaged_and_mixed_changes(self):
        self.repo.feature()
        for staged, unstaged in [(False, True), (True, False), (True, True)]:
            with self.subTest(staged=staged, unstaged=unstaged):
                self.repo.write("feature.py", "changed\n")
                if staged:
                    self.repo.git("add", "feature.py")
                if staged and unstaged:
                    self.repo.write("feature.py", "changed again\n")
                self.run_check(expected=1, reason="dirty_worktree")
                self.repo.git("reset", "--hard", "HEAD")

    def test_untracked_files_block_even_when_ignored_by_review(self):
        self.repo.feature()
        self.repo.write("vendor/untracked.py", "not committed\n")
        self.run_check(expected=1, reason="untracked_files")

    def test_untracked_output_exceptions(self):
        self.repo.feature()
        for path in ["review.md", "improve.md", "description.md"]:
            self.repo.write(path, "old local result\n")
        self.run_check()
        self.repo.write("nested/review.md", "not the configured output\n")
        self.run_check(expected=1, reason="untracked_files")

    def test_configured_absolute_and_relative_inside_outputs(self):
        self.repo.feature()
        paths = {"review": "results/review.md", "improve": str(self.repo.path / "results/improve.md"), "describe": "results/description.md"}
        for value in paths.values():
            self.repo.write(value, "prior output\n")
        result = self.run_check(probe=MockProbe(self.repo, paths=paths))
        self.assertEqual(result["output_paths"], {key: str((self.repo.path / value).resolve()) for key, value in paths.items()})

    def test_output_symlink_inside_is_resolved(self):
        self.repo.feature()
        self.repo.write("results/old.md", "prior output\n")
        (self.repo.path / "review.md").symlink_to("results/old.md")
        self.run_check()

    def test_tracked_output_collision(self):
        self.repo.write("review.md", "source\n")
        self.repo.feature()
        self.run_check(expected=1, reason="tracked_output_collision")

    def test_tracked_output_symlink_and_hardlink_collision(self):
        self.repo.feature()
        output = self.repo.path / "review.md"
        output.symlink_to("feature.py")
        self.run_check(expected=1, reason="tracked_output_collision")
        output.unlink()
        os.link(self.repo.path / "feature.py", output)
        self.run_check(expected=1, reason="tracked_output_collision")

    def test_external_output_paths_and_symlink_escape(self):
        self.repo.feature()
        for path in [str(Path(self.temp.name) / "outside.md"), "../outside.md"]:
            with self.subTest(path=path):
                paths = MockProbe(self.repo).paths
                paths["review"] = path
                self.run_check(probe=MockProbe(self.repo, paths), expected=2, reason="unsupported_external_output_path")
        (self.repo.path / "review.md").symlink_to(Path(self.temp.name) / "outside.md")
        self.run_check(expected=2, reason="unsupported_external_output_path")

    def test_git_metadata_output_rejected(self):
        self.repo.feature()
        paths = MockProbe(self.repo).paths
        paths["review"] = ".git/index"
        self.run_check(probe=MockProbe(self.repo, paths), expected=2, reason="invalid_output_path")

    def test_missing_base_and_invalid_revision(self):
        self.repo.feature()
        self.run_check(base="missing", expected=1, reason="missing_base")
        self.run_check(base="main~1", expected=2, reason="usage_error")
        self.run_check(base="refs/remotes/origin/main", expected=1, reason="missing_base")

    def test_default_main_then_master_and_explicit_local_base(self):
        self.repo.feature()
        self.repo.git("branch", "master", "main")
        self.assertEqual(self.run_check()["base"], "main")
        self.repo.git("branch", "-D", "main")
        self.assertEqual(self.run_check()["base"], "master")
        self.repo.git("branch", "stable", "master")
        self.assertEqual(self.run_check(base="stable")["base"], "stable")
        self.repo.git("branch", "-D", "master")
        self.run_check(expected=1, reason="missing_base")

    def test_detached_same_base_and_no_commits(self):
        self.run_check(expected=1, reason="no_branch_commits")
        self.repo.git("switch", "main")
        self.run_check(expected=1, reason="same_base_branch")
        self.repo.git("switch", "--detach")
        self.run_check(expected=1, reason="detached_head")

    def test_no_merge_base(self):
        self.repo.git("switch", "--orphan", "unrelated")
        self.repo.write("unrelated.py", "other history\n")
        self.repo.commit()
        self.run_check(expected=1, reason="no_merge_base")

    def test_spaces_tabs_newlines_and_modified_rename(self):
        original = "old file\tname\n.py"
        renamed = "new file\tname\n.py"
        self.repo.write(original, "".join(f"base_{i}\n" for i in range(20)))
        self.repo.commit("rename source")
        self.repo.git("branch", "-f", "main", "HEAD")
        self.repo.git("mv", "--", original, renamed)
        self.repo.write(renamed, "".join(f"base_{i}\n" for i in range(20)) + "added\n")
        for name in ["space name.py", "tab\tname.py", "line\nbreak.py"]:
            self.repo.write(name, "line\n")
        self.repo.commit()
        result = self.run_check()
        self.assertEqual(result["changed_files"], 4)
        self.assertEqual(result["changed_lines"], 4)
        self.assertEqual(set(result["reviewable_files"]), {renamed, "space name.py", "tab\tname.py", "line\nbreak.py"})

    def test_pure_rename_and_empty_patch_are_not_reviewable(self):
        self.repo.git("mv", "seed.txt", "renamed.txt")
        self.repo.commit()
        result = self.run_check(expected=1, reason="no_reviewable_input")
        self.assertEqual(result["excluded_files"], [{"path": "renamed.txt", "reason": "no_text_patch"}])

    def test_shared_exclusions_leave_no_input(self):
        self.repo.feature()
        result = self.run_check(
            probe=MockProbe(self.repo, exclusions={"feature.py": "shared_ignore_filter"}),
            expected=1, reason="no_reviewable_input",
        )
        self.assertEqual(result["changed_lines"], 0)

    def test_probe_failure_and_incomplete_patch_never_ok(self):
        self.repo.feature()
        def broken(*args, **kwargs):
            raise preflight.Failure("incomplete_shared_filters", "Could not load all ignore rules.")
        self.run_check(probe=broken, expected=2, reason="incomplete_shared_filters")
        normal = MockProbe(self.repo)
        def truncated(*args, **kwargs):
            response = normal(*args, **kwargs)
            if response["files"]:
                response["files"][0]["patch"] = "@@ -0,0 +1,2 @@\n+only one\n"
            return response
        self.run_check(probe=truncated, expected=2, reason="incomplete_provider_diff")

    def test_staged_rename_with_newline_blocks(self):
        self.repo.feature()
        self.repo.git("mv", "feature.py", "new\tname\n.py")
        self.run_check(expected=1, reason="dirty_worktree")

    def test_repository_changed_during_probe_never_ok(self):
        self.repo.feature()
        real = preflight.git_line
        calls = []
        def changed(repo, *args):
            value = real(repo, *args)
            if args[0] == "rev-parse" and "HEAD^{commit}" in args:
                calls.append(value)
                if len(calls) > 1:
                    return "0" * 40
            return value
        with mock.patch.object(preflight, "git_line", changed):
            self.run_check(expected=2, reason="repository_changed")

    def test_invalid_repository_and_unexpected_error_are_json(self):
        self.run_check(path=Path(self.temp.name), expected=2, reason="invalid_repository")
        self.repo.feature()
        def unexpected(*args, **kwargs):
            raise AttributeError("Do not print this exception value.")
        result = self.run_check(probe=unexpected, expected=2, reason="preflight_error")
        self.assertNotIn("Do not print", result["message"])

    def test_failed_git_command_never_ok(self):
        self.repo.feature()
        real = preflight.git
        def failed(repo, *args, **kwargs):
            if args[0] == "diff":
                raise preflight.Failure("git_command_failed", "Synthetic Git failure.")
            return real(repo, *args, **kwargs)
        with mock.patch.object(preflight, "git", failed):
            self.run_check(expected=2, reason="git_command_failed")

    def test_patch_hunk_count_handles_header_like_lines_and_control_chars(self):
        patch = "@@ -1,2 +1,2 @@\n---removed\n-old\vtext\n+++added\n+new\ftext\n\\ No newline at end of file\n"
        self.assertEqual(preflight.patch_changed_lines(patch), 4)

    def test_cli_usage_is_one_json_object_without_override(self):
        for args in [[], ["--help"], ["--repo", str(self.repo.path), "--max-changed-lines", "9999"]]:
            with self.subTest(args=args):
                proc = subprocess.run([sys.executable, "-B", str(SCRIPT), *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.assertEqual(proc.returncode, 2)
                value, end = json.JSONDecoder().raw_decode(proc.stdout.decode())
                self.assertEqual(proc.stdout.decode()[end:], "\n")
                self.assertEqual(value["reason"], "usage_error")
                self.assertEqual(proc.stderr, b"")

    def test_probe_invalid_or_failed_output(self):
        self.repo.feature()
        for code, stdout in [(0, b'{}\n{}\n'), (0, b'{}\n'), (1, b'{"ok":true}')]:
            with self.subTest(code=code, stdout=stdout):
                proc = subprocess.CompletedProcess([], code, stdout, b"not printed")
                with mock.patch.object(preflight.subprocess, "run", return_value=proc):
                    with self.assertRaises(preflight.Failure):
                        preflight.package_probe(self.repo.path)


@unittest.skipUnless(preflight.PR_AGENT_EXECUTABLE.exists(), "Installed PR-Agent interpreter is unavailable")
class InstalledSharedFilterTests(RepoTestCase):
    def test_offline_installed_filters_utf8_and_nul_safe_provider(self):
        files = {
            "feature.py": "source\n",
            "space tab\tand\nnewline.py": "source\n",
            "data.map": "review this map\n",
            "vendor/lib.py": "excluded\n",
            "openspec/changes/change.md": "excluded\n",
            "nested/uv.lock": "excluded\n",
            "package-lock.json": "excluded\n",
            "app.min.js": "excluded\n",
            "app.min.css": "excluded\n",
            "app.js.map": "excluded\n",
            "photo.png": b"\x89PNG\0binary",
            "binary.txt": b"hello\0world\n",
            "latin.txt": b"caf\xe9\n",
        }
        for name, content in files.items():
            self.repo.write(name, content)
        self.repo.commit()
        result = self.run_check(probe=preflight.package_probe)
        self.assertEqual(set(result["reviewable_files"]), {"feature.py", "space tab\tand\nnewline.py", "data.map"})
        self.assertEqual(result["changed_lines"], 3)
        excluded = {row["path"]: row["reason"] for row in result["excluded_files"]}
        self.assertEqual(excluded["vendor/lib.py"], "shared_ignore_filter")
        self.assertEqual(excluded["openspec/changes/change.md"], "shared_ignore_filter")
        for name in ["nested/uv.lock", "package-lock.json", "app.min.js", "app.min.css", "app.js.map", "photo.png"]:
            self.assertEqual(excluded[name], "shared_language_filter")
        self.assertEqual(excluded["binary.txt"], "binary_file")
        self.assertEqual(excluded["latin.txt"], "non_utf8_file")
        self.assertIn("LocalGitProvider", result["filter_source"]["provider"])

    def test_installed_configured_inside_output_paths(self):
        self.repo.feature()
        self.repo.write("results/review.md", "old result\n")
        self.repo.write("results/improve.md", "old result\n")
        env = {"LOCAL__REVIEW_PATH": "results/review.md", "LOCAL__IMPROVE_PATH": str(self.repo.path / "results/improve.md")}
        with mock.patch.dict(os.environ, env):
            result = self.run_check(probe=preflight.package_probe)
        self.assertEqual(result["output_paths"]["review"], str(self.repo.path / "results/review.md"))
        self.assertEqual(result["output_paths"]["improve"], str(self.repo.path / "results/improve.md"))

    def test_installed_nul_safe_modified_rename(self):
        original = "old space\tname\n.py"
        renamed = "new space\tname\n.py"
        self.repo.write(original, "".join(f"line_{i}\n" for i in range(20)))
        self.repo.commit("rename base")
        self.repo.git("branch", "-f", "main", "HEAD")
        self.repo.git("mv", "--", original, renamed)
        self.repo.write(renamed, "".join(f"line_{i}\n" for i in range(20)) + "new line\n")
        self.repo.commit()
        result = self.run_check(probe=preflight.package_probe)
        self.assertEqual(result["reviewable_files"], [renamed])
        self.assertEqual(result["changed_files"], 1)
        self.assertEqual(result["changed_lines"], 1)

    def test_installed_generated_rules_and_cli_glob_override(self):
        self.repo.write("generated/message_pb2.py", "generated\n")
        self.repo.feature()
        env = {"CONFIG__IGNORE_LANGUAGE_FRAMEWORK": '["protobuf"]', "IGNORE__GLOB": '["feature.py"]'}
        with mock.patch.dict(os.environ, env):
            result = self.run_check(probe=preflight.package_probe)
        self.assertEqual(result["reviewable_files"], ["feature.py"])
        self.assertEqual(result["excluded_files"], [{"path": "generated/message_pb2.py", "reason": "shared_ignore_filter"}])

    def test_installed_boundaries_and_script_json_stdout(self):
        self.repo.feature(2000)
        for count, code, reason in [(2000, 0, "ok"), (2001, 1, "changed_line_limit_exceeded")]:
            if count == 2001:
                self.repo.write("feature.py", "".join(f"line_{i}\n" for i in range(count)))
                self.repo.commit()
            before = self.repo.snapshot()
            proc = subprocess.run(
                [sys.executable, "-B", str(SCRIPT), "--repo", str(self.repo.path)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            self.assertEqual(proc.returncode, code, proc.stdout)
            result, end = json.JSONDecoder().raw_decode(proc.stdout.decode())
            self.assertEqual(proc.stdout.decode()[end:], "\n")
            self.assertEqual(proc.stderr, b"")
            self.assertEqual(result["changed_lines"], count)
            self.assertEqual(result["reason"], reason)
            self.assertEqual(before, self.repo.snapshot())

    def test_installed_provider_and_unknown_config_layers_fail_clearly(self):
        self.repo.feature()
        checks = [
            ({"CONFIG__GIT_PROVIDER": "github"}, "unsupported_git_provider"),
            ({"PR_AGENT_EXTRA_CONFIG_URL": "https://example.invalid/config.toml"}, "unsupported_config_layers"),
            ({"SETTINGS_FILE_FOR_DYNACONF": "/missing/settings.toml"}, "unsupported_config_layers"),
            ({"IGNORE__REGEX": '["["]'}, "incomplete_shared_filters"),
        ]
        for env, reason in checks:
            with self.subTest(env_names=list(env)):
                with mock.patch.dict(os.environ, env):
                    self.run_check(probe=preflight.package_probe, expected=2, reason=reason)


if __name__ == "__main__":
    unittest.main()

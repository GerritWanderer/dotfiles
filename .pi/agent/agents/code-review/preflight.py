#!/usr/bin/env python3
"""Check a local review without running PR-Agent commands or model calls."""

import argparse
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys

MAX_CHANGED_LINES = 2000
PR_AGENT_EXECUTABLE = Path("/home/gerrit/.local/bin/pr-agent")
PACKAGE_ROOT = Path("/home/gerrit/Work/tries/pr-agent/pr_agent")
USAGE = "python preflight.py --repo PATH [--base LOCAL_BRANCH]"

# These files define the audited configuration layers and local-provider behavior.
# Stop if they change. A new installation requires another read-only audit.
AUDITED_SOURCES = {
    "config_loader.py": "5d79a5dc5b2f8952cefd32cf75b5f43baeb60296477ed9ef4fafb61b7b105508",
    "custom_merge_loader.py": "238338300da6172ba94f4716a51ec4c91bf362d5189d3714ea260f397de9c785",
    "git_providers/local_git_provider.py": "ab3edf405043e55f7e45e3440e19f54f428163e822324360257f0f6b5cd72d85",
    "git_providers/utils.py": "e6196ac2937ade063a8928a107a3467c468cf9da466eba19c3945e8c2d0e65e8",
    "cli.py": "ef0bb70917cba0bee7eb12327f277d77deb70bd25a7655a0442ccef86239597f",
    "agent/pr_agent.py": "c2526ce8fe96bb3790833de233080075eaadd246df5ddc8534a899a943c21a22",
    "algo/cli_args.py": "592c74fcae31db3ba45fdaf2d96a374e33a405b2df74f6c77fb843e8b5edcc14",
    "config_security.py": "0f7d1c85332a52561f6823efec5aa4f5702b582f2dedde568fe3738a9f023571",
}

# Run this code with the installed interpreter, not the CLI entry point.
PACKAGE_PROBE = r'''
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import sys
import tomllib

sys.dont_write_bytecode = True
request = json.load(sys.stdin)

class ProbeError(Exception):
    def __init__(self, reason, message):
        self.reason, self.message = reason, message

def fail(reason, message):
    raise ProbeError(reason, message)

def audit(event, args):
    if event == "open":
        if args[0] == os.devnull or (isinstance(args[0], int) and stat.S_ISFIFO(os.fstat(args[0]).st_mode)):
            return
        mode, flags = args[1:3]
        if (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
            isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
        ):
            fail("probe_write_attempt", "The package probe attempted to write a file.")
    if event in {"os.remove", "os.rename", "os.mkdir", "os.rmdir", "os.link", "os.symlink", "os.chmod", "os.chown", "os.truncate", "os.utime"}:
        fail("probe_write_attempt", "The package probe attempted to change a file.")
    if event.startswith("socket.") or event in {"os.system", "os.exec", "os.posix_spawn"}:
        fail("probe_unsafe_operation", "The package probe attempted a network or shell operation.")
    if event == "subprocess.Popen":
        executable, argv = args[:2]
        commands = {"version", "rev-parse", "diff", "diff-tree", "cat-file", "for-each-ref", "symbolic-ref", "show-ref", "merge-base", "status"}
        if Path(executable).name != "git" or not isinstance(argv, (list, tuple)):
            fail("probe_unsafe_operation", "Only read-only Git commands are permitted in the package probe.")
        i = 1
        while i < len(argv) and argv[i] == "-c":
            i += 2
        if i >= len(argv) or (argv[i] not in commands and argv[i] != "--version"):
            fail("probe_unsafe_operation", "The package probe attempted an unsupported Git command.")

sys.addaudithook(audit)

def probe():
    root = Path(request["package_root"])
    for filename, digest in request["audited_sources"].items():
        if hashlib.sha256((root / filename).read_bytes()).hexdigest() != digest:
            fail("unsupported_config_layers", "Installed configuration or provider code changed; audit the package before use.")
    spec = importlib.util.find_spec("pr_agent")
    if spec is None or root not in [Path(p).resolve() for p in (spec.submodule_search_locations or [])]:
        fail("package_not_found", "The installed interpreter does not resolve the audited PR-Agent package.")

    # Reject loader selection and lazy environment values before Dynaconf starts.
    for key, value in os.environ.items():
        name = key.upper()
        if name.startswith("DYNACONF_") or (name.endswith("_FOR_DYNACONF") and name != "AUTO_CAST_FOR_DYNACONF"):
            fail("unsupported_config_layers", "Dynaconf control environment variables are not supported.")
        if name in {"SETTINGS_FILE", "SETTINGS_FILES", "SETTINGS_MODULE", "INCLUDES", "PRELOAD", "LOADERS", "CORE_LOADERS", "ROOT_PATH", "ENVVAR_PREFIX", "FRESH_VARS", "FILTER_STRATEGY"}:
            fail("unsupported_config_layers", "Environment-selected configuration loaders are not supported.")
        if value.lstrip().startswith(("@format", "@jinja", "@get", "@read", "@merge", "@reset", "@del")):
            fail("unsupported_config_layers", "Dynamic environment configuration is not supported.")
    if os.environ.get("PR_AGENT_EXTRA_CONFIG_URL", "").strip():
        fail("unsupported_config_layers", "Extra configuration sources cannot be resolved by this read-only probe.")

    from loguru import logger
    logger.remove()
    warnings = []
    logger.add(lambda message: warnings.append(message.record), level="WARNING")
    from pr_agent.config_loader import get_settings, dynconf_kwargs
    from pr_agent.custom_merge_loader import load, validate_file_security, MAX_TOML_SIZE_IN_BYTES
    from dynaconf.loaders import env_loader

    if dynconf_kwargs.get("loaders") != ["pr_agent.custom_merge_loader", "dynaconf.loaders.env_loader"] or dynconf_kwargs.get("core_loaders") != []:
        fail("unsupported_config_layers", "The installed configuration loaders are not supported.")
    settings = get_settings()
    files = settings.get("SETTINGS_FILE_FOR_DYNACONF")
    if not isinstance(files, list) or not files:
        fail("unsupported_config_layers", "The installed settings-file selection is not supported.")
    optional = {root / "settings/.secrets.toml", root / "settings_prod/.secrets.toml"}
    for name in files:
        path = Path(name)
        if not path.is_absolute() or path.parent not in {root / "settings", root / "settings/code_suggestions", root / "settings_prod"}:
            fail("unsupported_config_layers", "A settings file is outside the audited package settings directories.")
        if not path.exists():
            if path in optional:
                continue
            fail("invalid_configuration", "A required package settings file is missing.")
        if path.stat().st_size > MAX_TOML_SIZE_IN_BYTES:
            fail("invalid_configuration", "A package settings file exceeds the loader size limit.")
        try:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
            validate_file_security(data, str(path))
        except Exception:
            fail("invalid_configuration", "A package settings file failed TOML or security validation.")
        if any(not isinstance(value, dict) for value in data.values()):
            fail("invalid_configuration", "A package settings section is not a table.")
    try:
        # Replay with errors enabled. The normal loader can skip invalid files.
        load(settings, silent=False)
        env_loader.load(settings, silent=False)
    except Exception:
        fail("invalid_configuration", "Installed settings or environment overrides could not be loaded completely.")
    allowed_warnings = {f"Settings file not found: {path}. Skipping it." for path in optional if not path.exists()}
    if any(str(record["message"]) not in allowed_warnings for record in warnings):
        fail("invalid_configuration", "Installed configuration loading reported an unexpected warning or error.")
    warnings.clear()

    if settings.get("config.git_provider") != "local":
        fail("unsupported_git_provider", "The effective config.git_provider must already be local; the CLI cannot override it.")
    if settings.get("config.secret_provider", ""):
        fail("unsupported_config_layers", "Secret-provider configuration is not resolved by this offline probe.")
    if settings.get("config.extra_config_url") or settings.get("config.enable_per_directory_settings", False):
        fail("unsupported_config_layers", "Extra or per-directory configuration layers are not supported.")

    from pr_agent.algo.cli_args import CliArgs
    from pr_agent.algo.utils import update_settings_from_args
    overrides = ['--ignore.glob=["vendor/**","openspec/**"]', '--config.propagate_tool_errors=true']
    if not CliArgs.validate_user_args(overrides)[0]:
        fail("unsupported_cli_overrides", "The installed CLI does not permit the required ignore and error-propagation overrides.")
    if update_settings_from_args(overrides):
        fail("unsupported_cli_overrides", "The installed CLI did not consume the required overrides.")

    def string_list(value, name):
        if isinstance(value, str):
            return
        if not isinstance(value, (list, tuple)) or any(not isinstance(item, str) for item in value):
            fail("invalid_configuration", name + " must contain strings.")

    string_list(settings.get("bad_extensions.default"), "bad_extensions.default")
    extra = settings.get("config.use_extra_bad_extensions")
    if not isinstance(extra, bool):
        fail("invalid_configuration", "config.use_extra_bad_extensions must be a boolean.")
    if extra:
        string_list(settings.get("bad_extensions.extra"), "bad_extensions.extra")

    repo = Path(request["repo"])
    paths = {}
    for tool, key, default in [("review", "review_path", "review.md"), ("improve", "improve_path", "improve.md"), ("describe", "description_path", "description.md")]:
        value = settings.get("local." + key)
        if value is None:
            value = str(repo / default)
        if not isinstance(value, str) or not value or "\0" in value:
            fail("invalid_output_path", "Local output paths must be nonempty filesystem paths.")
        path = Path(value)
        paths[tool] = str((repo / path).resolve())

    from pr_agent.algo.file_filter import filter_ignored_with_status
    from pr_agent.algo.language_handler import partition_files_by_language_filter
    from pr_agent.algo.types import FilePatchInfo
    candidates = [FilePatchInfo("", "", "", row["path"]) for row in request.get("files", [])]
    kept, complete = filter_ignored_with_status(candidates, platform="local")
    if not complete:
        fail("incomplete_shared_filters", "Installed ignore rules could not be evaluated completely.")
    valid, language_excluded = partition_files_by_language_filter(kept)
    if warnings:
        fail("incomplete_shared_filters", "Installed shared filters reported a warning or error.")
    result = {
        "output_paths": paths,
        "filter_source": {
            "package": str(root), "provider": "LocalGitProvider",
            "ignore": "pr_agent.algo.file_filter.filter_ignored_with_status(local)",
            "language": "pr_agent.algo.language_handler.partition_files_by_language_filter",
            "overrides": overrides,
            "config_layers": "audited installed TOML + environment; local provider has no repo-settings payload",
        },
        "files": [],
    }
    if request.get("base") is None:
        return result

    from pr_agent.git_providers.local_git_provider import LocalGitProvider
    provider = LocalGitProvider(request["base"])
    try:
        if str(provider.repo_path.resolve()) != str(repo):
            fail("probe_repository_mismatch", "The local provider found a different repository.")
        if provider.repo.head.commit.hexsha != request["head"] or provider.repo.commit(request["base"]).hexsha != request["base_head"]:
            fail("repository_changed", "Branch heads changed during the package probe.")
        provider_paths = {"review": provider.review_path, "improve": provider.improve_path, "describe": provider.description_path}
        if {key: str((repo / Path(value)).resolve()) for key, value in provider_paths.items()} != paths:
            fail("unsupported_config_layers", "Local output-path resolution differs from the audited provider.")
        patches = {}
        for file in provider.get_diff_files():
            if file.filename in patches:
                fail("incomplete_provider_diff", "The local provider returned duplicate diff paths.")
            patches[file.filename] = file.patch
        if any("Skipping non-UTF-8 file in local diff:" not in str(record["message"]) for record in warnings):
            fail("incomplete_provider_diff", "The local provider reported a diff error.")
        ignore_kept = {file.filename for file in kept}
        language_kept = {file.filename for file in valid}
        known_paths = {row["path"] for row in request["files"]}
        if not set(patches).issubset(known_paths):
            fail("incomplete_provider_diff", "The provider diff paths do not match the NUL-safe Git diff.")
        for row in request["files"]:
            path = row["path"]
            reason = None
            if path not in ignore_kept:
                reason = "shared_ignore_filter"
            elif path not in language_kept:
                reason = "shared_language_filter"
            elif any(mode not in {"000000", "100644", "100755", "120000"} for mode in row["modes"]):
                reason = "non_text_file"
            else:
                for oid in row["oids"]:
                    if set(oid) == {"0"}:
                        continue
                    content = provider.repo.odb.stream(bytes.fromhex(oid)).read()
                    if b"\0" in content:
                        reason = "binary_file"
                        break
                    try:
                        content.decode("utf-8")
                    except UnicodeDecodeError:
                        reason = "non_utf8_file"
                        break
            if reason is not None:
                result["files"].append({"path": path, "reason": reason})
            elif path not in patches:
                fail("incomplete_provider_diff", "A reviewable file is missing from the installed local-provider diff.")
            else:
                result["files"].append({"path": path, "patch": patches[path]})
    finally:
        provider.repo.close()
    return result

try:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        result = probe()
    response = {"ok": True, "result": result}
except ProbeError as exc:
    response = {"ok": False, "reason": exc.reason, "message": exc.message}
except Exception as exc:
    # Do not print exception values. A loader exception can contain credentials.
    response = {"ok": False, "reason": "package_probe_error", "message": "Read-only package probe failed (" + type(exc).__name__ + ")."}
print(json.dumps(response, ensure_ascii=True))
'''


class Failure(Exception):
    def __init__(self, reason, message, code=2):
        super().__init__(message)
        self.reason, self.message, self.code = reason, message, code


def readonly_environment():
    env = os.environ.copy()
    unsafe = {
        "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_NAMESPACE", "GIT_CONFIG",
        "GIT_CONFIG_COUNT", "GIT_CONFIG_PARAMETERS", "GIT_COMMON_DIR",
        "GIT_CEILING_DIRECTORIES", "GIT_DISCOVERY_ACROSS_FILESYSTEM",
        "GIT_EXTERNAL_DIFF", "GIT_DIFF_OPTS", "GIT_REPLACE_REF_BASE",
        "GIT_EXEC_PATH", "GIT_CONFIG_SYSTEM", "GIT_CONFIG_GLOBAL",
        "GIT_CONFIG_NOSYSTEM", "GIT_ATTR_SOURCE", "GIT_SHALLOW_FILE",
        "GIT_GRAFT_FILE", "GIT_PYTHON_GIT_EXECUTABLE",
    }
    if any(key in env for key in unsafe):
        raise Failure("unsupported_git_environment", "Git repository, configuration, or executable overrides are not supported.")
    env.update({
        "GIT_OPTIONAL_LOCKS": "0", "PYTHONDONTWRITEBYTECODE": "1",
        "GIT_TERMINAL_PROMPT": "0", "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_CONFIG_COUNT": "2", "GIT_CONFIG_KEY_0": "core.fsmonitor",
        "GIT_CONFIG_VALUE_0": "false", "GIT_CONFIG_KEY_1": "diff.ignoreSubmodules",
        "GIT_CONFIG_VALUE_1": "none",
    })
    return env


def git(repo, *args, accepted=(0,)):
    executable = shutil.which("git")
    if executable is None:
        raise Failure("git_unavailable", "Git is not installed.")
    try:
        proc = subprocess.run(
            [executable, "-C", str(repo), *args], env=readonly_environment(),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise Failure("git_command_failed", "A read-only Git command could not finish.") from None
    if proc.returncode not in accepted:
        raise Failure("git_command_failed", "A read-only Git command failed: " + args[0] + ".")
    return proc


def git_line(repo, *args):
    output = git(repo, *args).stdout
    if not output.endswith(b"\n"):
        raise Failure("invalid_git_output", "Git did not return the expected single-line result.")
    return os.fsdecode(output[:-1])


def package_probe(repo, base=None, files=None, head=None, base_head=None):
    try:
        with PR_AGENT_EXECUTABLE.open("rb") as handle:
            shebang = handle.readline(4096).decode("utf-8").strip()
        words = shlex.split(shebang[2:]) if shebang.startswith("#!") else []
        if len(words) != 1 or not Path(words[0]).is_absolute() or "python" not in Path(words[0]).name:
            raise Failure("unsupported_package_interpreter", "The installed PR-Agent executable must have an absolute Python shebang.")
        proc = subprocess.run(
            [words[0], "-I", "-B", "-c", PACKAGE_PROBE], cwd=repo,
            env=readonly_environment(), input=json.dumps({
                "repo": str(repo), "base": base, "files": files or [],
                "head": head, "base_head": base_head,
                "package_root": str(PACKAGE_ROOT), "audited_sources": AUDITED_SOURCES,
            }, ensure_ascii=True).encode("utf-8"),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60,
        )
    except Failure:
        raise
    except (OSError, ValueError, UnicodeError, subprocess.TimeoutExpired):
        raise Failure("package_probe_error", "The installed read-only package probe could not finish.") from None
    if proc.returncode != 0:
        raise Failure("package_probe_error", "The installed read-only package probe exited unsuccessfully.")
    try:
        response = json.loads(proc.stdout)
        if not isinstance(response, dict) or type(response.get("ok")) is not bool:
            raise ValueError
        if not response["ok"]:
            reason = response["reason"]
            message = response["message"]
            if not isinstance(reason, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", reason) or not isinstance(message, str):
                raise ValueError
            raise Failure(reason, message)
        result = response["result"]
        if not isinstance(result, dict) or not isinstance(result.get("files"), list) or not isinstance(result.get("filter_source"), dict):
            raise ValueError
        if set(result.get("output_paths", {})) != {"review", "improve", "describe"}:
            raise ValueError
        return result
    except (ValueError, KeyError, TypeError):
        raise Failure("invalid_probe_output", "The package probe did not return exactly one valid JSON object.") from None


def raw_diff(repo, merge_base, head):
    data = git(repo, "diff", "--raw", "-z", "--no-abbrev", "--no-ext-diff", "--no-textconv", "--find-renames", merge_base, head, "--").stdout
    fields = data.split(b"\0")
    if fields.pop() != b"":
        raise Failure("invalid_git_output", "The Git diff is not NUL-terminated.")
    rows = []
    i = 0
    while i < len(fields):
        metadata = fields[i].split(b" ")
        i += 1
        if len(metadata) != 5 or not metadata[0].startswith(b":") or i >= len(fields):
            raise Failure("invalid_git_output", "The NUL-safe Git diff metadata is invalid.")
        mode_a, mode_b, oid_a, oid_b, status = metadata
        old_path = fields[i]
        i += 1
        path = old_path
        if status.startswith((b"R", b"C")):
            if i >= len(fields):
                raise Failure("invalid_git_output", "A Git rename is missing its destination path.")
            path = fields[i]
            i += 1
        if not path:
            raise Failure("invalid_git_output", "A Git diff path is empty.")
        rows.append({
            "path": os.fsdecode(path), "old_path": os.fsdecode(old_path),
            "modes": [mode_a[1:].decode("ascii"), mode_b.decode("ascii")],
            "oids": [oid_a.decode("ascii"), oid_b.decode("ascii")],
        })
    return rows


def status(repo):
    return git(repo, "status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignored=no", "--ignore-submodules=none").stdout


def check_clean(repo, data, outputs):
    fields = data.split(b"\0")
    if fields.pop() != b"":
        raise Failure("invalid_git_output", "The Git status is not NUL-terminated.")
    i = 0
    untracked = []
    dirty = False
    while i < len(fields):
        entry = fields[i]
        i += 1
        if len(entry) < 4 or entry[2:3] != b" ":
            raise Failure("invalid_git_output", "The NUL-safe Git status is invalid.")
        xy, path = entry[:2], os.fsdecode(entry[3:])
        if xy == b"??":
            if (repo / path).resolve() not in outputs:
                untracked.append(path)
        else:
            dirty = True
            if b"R" in xy or b"C" in xy:
                if i >= len(fields):
                    raise Failure("invalid_git_output", "A status rename is missing its origin path.")
                i += 1
    if dirty:
        raise Failure("dirty_worktree", "Tracked, staged, or unstaged changes must be committed or removed before review.", 1)
    if untracked:
        raise Failure("untracked_files", "Untracked files exist outside the resolved local output paths.", 1)


def checked_output_paths(repo, values):
    if not isinstance(values, dict) or set(values) != {"review", "improve", "describe"}:
        raise Failure("invalid_probe_output", "The package probe did not resolve all three output paths.")
    paths = {}
    for key, value in values.items():
        if not isinstance(value, str) or not value or "\0" in value:
            raise Failure("invalid_output_path", "A local output path is invalid.")
        path = (repo / value).resolve()
        if not path.is_relative_to(repo):
            raise Failure("unsupported_external_output_path", "Local output paths must resolve inside the canonical reviewed repository.")
        if path == repo or path.is_dir():
            raise Failure("invalid_output_path", "A local output path refers to a directory.")
        paths[key] = path
    git_dir = Path(git_line(repo, "rev-parse", "--absolute-git-dir")).resolve()
    for path in paths.values():
        if path == repo / ".git" or path.is_relative_to(git_dir):
            raise Failure("invalid_output_path", "Local outputs must not overwrite Git metadata.")
    data = git(repo, "ls-files", "-z", "--cached").stdout
    if data and not data.endswith(b"\0"):
        raise Failure("invalid_git_output", "The tracked-file list is not NUL-terminated.")
    for entry in data.split(b"\0")[:-1]:
        tracked = repo / os.fsdecode(entry)
        for key, path in paths.items():
            configured = repo / values[key]
            if tracked == configured or tracked.resolve() == path:
                raise Failure("tracked_output_collision", "A local output path is tracked or resolves to a tracked source file.", 1)
            if tracked.exists() and path.exists() and os.path.samefile(tracked, path):
                raise Failure("tracked_output_collision", "A local output path is a hard link to a tracked source file.", 1)
    return paths


def patch_changed_lines(patch):
    """Count hunk additions and deletions. Check each hunk's declared lengths."""
    if not isinstance(patch, str):
        raise Failure("invalid_probe_output", "A provider patch is not UTF-8 text.")
    count = 0
    remaining = None
    lines = patch.split("\n")
    for index, line in enumerate(lines):
        if line.startswith("@@"):
            if remaining is not None and remaining != [0, 0]:
                raise Failure("incomplete_provider_diff", "A provider patch hunk is incomplete.")
            match = re.match(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?: |$)", line)
            if not match:
                raise Failure("incomplete_provider_diff", "A provider patch hunk header is invalid.")
            remaining = [int(match[2] or 1), int(match[4] or 1)]
        elif remaining is None:
            continue
        elif line.startswith("\\ No newline at end of file"):
            continue
        elif not line and index == len(lines) - 1:
            continue
        elif line.startswith("+"):
            count += 1
            remaining[1] -= 1
        elif line.startswith("-"):
            count += 1
            remaining[0] -= 1
        elif line.startswith(" "):
            remaining[0] -= 1
            remaining[1] -= 1
        else:
            raise Failure("incomplete_provider_diff", "A provider patch has an invalid hunk line.")
        if remaining is not None and min(remaining) < 0:
            raise Failure("incomplete_provider_diff", "A provider patch exceeds its declared hunk lengths.")
    if remaining is not None and remaining != [0, 0]:
        raise Failure("incomplete_provider_diff", "A provider patch hunk is incomplete.")
    return count


def empty_result():
    return {
        "ok": False, "reason": "usage_error", "message": USAGE,
        "repo": None, "branch": None, "base": None, "head": None,
        "base_head": None, "merge_base": None, "commits": None,
        "changed_files": 0, "reviewable_files": [], "changed_lines": 0,
        "max_changed_lines": MAX_CHANGED_LINES, "excluded_files": [],
        "output_paths": {"review": None, "improve": None, "describe": None},
        "filter_source": None,
    }


class JsonParser(argparse.ArgumentParser):
    def error(self, message):
        raise Failure("usage_error", message + ". Usage: " + USAGE)


def evaluate(repo_path, base, result):
    try:
        path = Path(repo_path).resolve(strict=True)
    except OSError:
        raise Failure("invalid_repository", "The repository path does not exist.") from None
    if not path.is_dir():
        raise Failure("invalid_repository", "The repository path is not a directory.")
    inside = git(path, "rev-parse", "--is-inside-work-tree", accepted=(0, 128))
    if inside.returncode or inside.stdout != b"true\n":
        raise Failure("invalid_repository", "The path is not inside a non-bare Git working tree.")
    repo = Path(git_line(path, "rev-parse", "--show-toplevel")).resolve()
    result["repo"] = str(repo)
    branch = git(repo, "symbolic-ref", "--quiet", "--short", "HEAD", accepted=(0, 1))
    if branch.returncode:
        raise Failure("detached_head", "The current branch is detached.", 1)
    result["branch"] = os.fsdecode(branch.stdout[:-1])
    if base is None:
        for candidate in ("main", "master"):
            found = git(repo, "show-ref", "--verify", "--quiet", "refs/heads/" + candidate, accepted=(0, 1))
            if not found.returncode:
                base = candidate
                break
        if base is None:
            raise Failure("missing_base", "No local main or master branch exists; select a local base with --base.", 1)
    result["base"] = base
    valid = git(repo, "check-ref-format", "refs/heads/" + base, accepted=(0, 1))
    if valid.returncode:
        raise Failure("usage_error", "--base must name a local branch, not a revision or remote ref.")
    base_ref = "refs/heads/" + base
    found = git(repo, "show-ref", "--verify", "--quiet", base_ref, accepted=(0, 1))
    if found.returncode:
        raise Failure("missing_base", "The selected local base branch does not exist.", 1)
    result["base_head"] = git_line(repo, "rev-parse", "--verify", base_ref + "^{commit}")
    result["head"] = git_line(repo, "rev-parse", "--verify", "HEAD^{commit}")
    if result["branch"] == base:
        raise Failure("same_base_branch", "Switch to a feature branch before review.", 1)
    merge = git(repo, "merge-base", "--all", result["base_head"], result["head"], accepted=(0, 1))
    if merge.returncode:
        raise Failure("no_merge_base", "The current branch and local base have no merge base.", 1)
    merges = merge.stdout.decode("ascii").splitlines()
    if len(merges) != 1:
        raise Failure("ambiguous_merge_base", "The review requires one unambiguous merge base.")
    result["merge_base"] = merges[0]
    result["commits"] = int(git_line(repo, "rev-list", "--count", result["base_head"] + ".." + result["head"]))
    if not result["commits"]:
        raise Failure("no_branch_commits", "The current branch has no commits outside the local base.", 1)

    config = package_probe(repo)
    result["output_paths"] = config["output_paths"]
    result["filter_source"] = config["filter_source"]
    outputs = checked_output_paths(repo, config["output_paths"])
    result["output_paths"] = {key: str(path) for key, path in outputs.items()}
    initial_status = status(repo)
    check_clean(repo, initial_status, set(outputs.values()))
    rows = raw_diff(repo, result["merge_base"], result["head"])
    result["changed_files"] = len(rows)
    diff = package_probe(repo, base, rows, result["head"], result["base_head"])
    if diff["output_paths"] != config["output_paths"] or diff["filter_source"] != config["filter_source"]:
        raise Failure("configuration_changed", "Effective output paths or filters changed during preflight.")
    expected = {row["path"] for row in rows}
    seen = set()
    for file in diff["files"]:
        if not isinstance(file, dict) or not isinstance(file.get("path"), str) or file["path"] not in expected or file["path"] in seen:
            raise Failure("invalid_probe_output", "The package probe returned an incomplete or duplicate file list.")
        seen.add(file["path"])
        if "reason" in file:
            if not isinstance(file["reason"], str) or not re.fullmatch(r"[a-z][a-z0-9_]*", file["reason"]):
                raise Failure("invalid_probe_output", "An excluded file has an invalid reason.")
            result["excluded_files"].append({"path": file["path"], "reason": file["reason"]})
            continue
        lines = patch_changed_lines(file.get("patch"))
        if not lines:
            result["excluded_files"].append({"path": file["path"], "reason": "no_text_patch"})
        else:
            result["reviewable_files"].append(file["path"])
            result["changed_lines"] += lines
    if seen != expected:
        raise Failure("incomplete_provider_diff", "The package probe omitted changed files.")
    if git_line(repo, "rev-parse", "HEAD^{commit}") != result["head"] or git_line(repo, "rev-parse", base_ref + "^{commit}") != result["base_head"] or git_line(repo, "symbolic-ref", "--quiet", "--short", "HEAD") != result["branch"] or status(repo) != initial_status:
        raise Failure("repository_changed", "The branch or working tree changed during preflight.")
    checked_output_paths(repo, config["output_paths"])
    if not result["reviewable_files"]:
        raise Failure("no_reviewable_input", "No reviewable UTF-8 text patch remains after the installed shared filters.", 1)
    if result["changed_lines"] > MAX_CHANGED_LINES:
        raise Failure("changed_line_limit_exceeded", "The reviewable patch exceeds the fixed 2000 added-plus-deleted-line limit. This cap is not a token guarantee.", 1)
    result.update(ok=True, reason="ok", message="Clean local feature branch is within the 2000 changed-line limit. This cap is not a token guarantee.")


def main(argv=None):
    result = empty_result()
    code = 2
    try:
        parser = JsonParser(add_help=False, allow_abbrev=False)
        parser.add_argument("--repo", required=True)
        parser.add_argument("--base")
        args = parser.parse_args(argv)
        evaluate(args.repo, args.base, result)
        code = 0
    except Failure as exc:
        result.update(ok=False, reason=exc.reason, message=exc.message)
        code = exc.code
    except Exception as exc:
        result.update(ok=False, reason="preflight_error", message="Read-only preflight failed (" + type(exc).__name__ + ").")
    print(json.dumps(result, ensure_ascii=True))
    return code


if __name__ == "__main__":
    sys.exit(main())

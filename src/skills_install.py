from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from config.config import PROJECT_ROOT

AGENT_MAP: dict[str, tuple[str, str]] = {
    "cursor": (".cursor", ".cursor/skills"),
    "claude": (".claude", ".claude/skills"),
    "codex": (".codex", ".codex/skills"),
    "windsurf": (".windsurf", ".windsurf/skills"),
    "continue": (".continue", ".continue/skills"),
    "augment": (".augment", ".augment/skills"),
    "roo": (".roo", ".roo/skills"),
    "gemini": (".gemini", ".gemini/skills"),
    "copilot": (".copilot", ".copilot/skills"),
    "factory": (".factory", ".factory/skills"),
}

CLI_LOCAL_SKILLS_DIR = PROJECT_ROOT / "skills"
DEFAULT_CANONICAL_DIR = Path.home() / ".agents" / "skills"
DEFAULT_LOCKFILE = Path.home() / ".agents" / ".skill-lock.json"
SKILL_FOLDER_PREFIX = "olostep-"


@dataclass(frozen=True)
class SkillEntry:
    name: str
    sanitized_name: str
    description: str
    source_dir: Path
    skill_md_path: Path


@dataclass
class InstallOptions:
    source: Path
    cli_local_dir: Path
    canonical_dir: Path
    lockfile_path: Path
    agent: list[str]
    all_agents: bool
    global_install: bool
    agent_skills_dir: Path | None
    skill: list[str]
    exclude: list[str]
    dry_run: bool
    overwrite: bool
    link_mode: Literal["auto", "symlink", "copy"]
    yes: bool


@dataclass
class RemoveOptions:
    canonical_dir: Path
    lockfile_path: Path
    agent: list[str]
    all_agents: bool
    agent_skills_dir: Path | None
    skill: list[str]
    dry_run: bool
    yes: bool


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def to_prefixed_folder_name(raw: str) -> str:
    sanitized = sanitize_name(raw)
    if sanitized.startswith(SKILL_FOLDER_PREFIX):
        return sanitized
    return f"{SKILL_FOLDER_PREFIX}{sanitized}"


def sanitize_name(raw: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9._-]+", "-", raw.strip().lower())
    clean = re.sub(r"-{2,}", "-", clean).strip("-")
    if not clean:
        raise ValueError(f"Invalid skill name: {raw!r}")
    return clean


def parse_skill_frontmatter(skill_md_path: Path) -> dict[str, str]:
    content = skill_md_path.read_text(encoding="utf-8")
    if not content.startswith("---\n"):
        raise ValueError(f"Missing frontmatter in {skill_md_path}")
    end = content.find("\n---\n", 4)
    if end == -1:
        raise ValueError(f"Unterminated frontmatter in {skill_md_path}")
    block = content[4:end].strip()
    values: dict[str, str] = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip()
    if not values.get("name"):
        raise ValueError(f"Missing frontmatter field 'name' in {skill_md_path}")
    if not values.get("description"):
        raise ValueError(f"Missing frontmatter field 'description' in {skill_md_path}")
    return values


def sync_plugin_skills_to_cli_local(
    plugin_source_dir: Path, cli_local_dir: Path, *, dry_run: bool
) -> dict[str, object]:
    if not plugin_source_dir.is_dir():
        raise ValueError(f"Plugin skills source not found: {plugin_source_dir}")
    skill_files = sorted(plugin_source_dir.glob("*/SKILL.md"))
    if not skill_files:
        raise ValueError(f"No skills found in plugin source: {plugin_source_dir}")
    same_source_and_target = plugin_source_dir.resolve() == cli_local_dir.resolve()
    if not dry_run and not same_source_and_target:
        if cli_local_dir.exists():
            shutil.rmtree(cli_local_dir)
        shutil.copytree(plugin_source_dir, cli_local_dir)
    return {
        "plugin_source_dir": str(plugin_source_dir),
        "cli_local_dir": str(cli_local_dir),
        "skills_found": len(skill_files),
        "copied_to_cli_local": not same_source_and_target,
    }


def discover_skills(source_dir: Path) -> list[SkillEntry]:
    if not source_dir.is_dir():
        raise ValueError(f"Skills source not found: {source_dir}")
    entries: list[SkillEntry] = []
    seen_sanitized: set[str] = set()
    for skill_md in sorted(source_dir.glob("*/SKILL.md")):
        fm = parse_skill_frontmatter(skill_md)
        name = fm["name"]
        sanitized = sanitize_name(name)
        if sanitized in seen_sanitized:
            raise ValueError(f"Duplicate sanitized skill name '{sanitized}' in {skill_md}")
        seen_sanitized.add(sanitized)
        entries.append(
            SkillEntry(
                name=name,
                sanitized_name=sanitized,
                description=fm["description"],
                source_dir=skill_md.parent,
                skill_md_path=skill_md,
            )
        )
    if not entries:
        raise ValueError(f"No valid skills found in {source_dir}")
    return entries


def detect_installed_agents() -> list[str]:
    home = Path.home()
    installed: list[str] = []
    for agent, (probe_dir, _) in AGENT_MAP.items():
        if (home / probe_dir).exists():
            installed.append(agent)
    return installed


def _dir_hash(path: Path) -> str:
    hasher = hashlib.sha256()
    for file_path in sorted(path.rglob("*")):
        if not file_path.is_file():
            continue
        rel = file_path.relative_to(path).as_posix()
        hasher.update(rel.encode("utf-8"))
        hasher.update(file_path.read_bytes())
    return hasher.hexdigest()


def _should_install_skill(skill: SkillEntry, include: set[str], exclude: set[str]) -> bool:
    key = sanitize_name(skill.name)
    if include and key not in include:
        return False
    if key in exclude:
        return False
    return True


def _resolve_target_agents(options: InstallOptions) -> list[str]:
    return _resolve_targets(options.agent_skills_dir, options.agent, options.all_agents)


def _resolve_targets(agent_skills_dir: Path | None, agents: list[str], all_agents: bool) -> list[str]:
    if agent_skills_dir:
        return ["custom"]
    if agents:
        unknown = [x for x in agents if x not in AGENT_MAP]
        if unknown:
            raise ValueError(f"Unknown agent(s): {', '.join(sorted(unknown))}")
        return sorted(set(agents))
    if not all_agents:
        return []
    return detect_installed_agents()


def _safe_replace_dir(dst: Path, *, overwrite: bool, dry_run: bool) -> None:
    if dst.exists():
        if not overwrite:
            raise ValueError(f"Target exists and overwrite is disabled: {dst}")
        if not dry_run:
            if dst.is_symlink() or dst.is_file():
                dst.unlink()
            else:
                shutil.rmtree(dst)


def _install_to_canonical(skill: SkillEntry, canonical_dir: Path, *, overwrite: bool, dry_run: bool) -> Path:
    dst = canonical_dir / to_prefixed_folder_name(skill.sanitized_name)
    _safe_replace_dir(dst, overwrite=overwrite, dry_run=dry_run)
    if not dry_run:
        canonical_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(skill.source_dir, dst)
    return dst


def _install_to_agent_dir(
    canonical_skill_dir: Path,
    agent_skill_dir: Path,
    skill_folder_name: str,
    *,
    overwrite: bool,
    dry_run: bool,
    link_mode: Literal["auto", "symlink", "copy"],
) -> str:
    dst = agent_skill_dir / skill_folder_name
    _safe_replace_dir(dst, overwrite=overwrite, dry_run=dry_run)
    if dry_run:
        return "dry-run"
    agent_skill_dir.mkdir(parents=True, exist_ok=True)
    if link_mode in ("auto", "symlink"):
        try:
            # Use absolute source path so symlinks remain valid regardless of current cwd.
            os.symlink(canonical_skill_dir.resolve(), dst, target_is_directory=True)
            return "symlink"
        except OSError:
            if link_mode == "symlink":
                raise
    shutil.copytree(canonical_skill_dir, dst)
    return "copy"


def _load_lockfile(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"version": 1, "skills": {}}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"version": 1, "skills": {}}
    if not isinstance(parsed, dict):
        return {"version": 1, "skills": {}}
    skills = parsed.get("skills")
    if not isinstance(skills, dict):
        parsed["skills"] = {}
    if "version" not in parsed:
        parsed["version"] = 1
    return parsed


def _write_lockfile(path: Path, lock_data: dict[str, object], *, dry_run: bool) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(lock_data, indent=2) + "\n", encoding="utf-8")


def run_install(options: InstallOptions) -> dict[str, object]:
    if options.agent and not options.global_install:
        raise ValueError("--agent requires --global")
    if options.agent_skills_dir and options.global_install:
        raise ValueError("--agent-skills-dir cannot be combined with --global")

    sync_result = sync_plugin_skills_to_cli_local(
        options.source,
        options.cli_local_dir,
        dry_run=options.dry_run,
    )
    discover_dir = options.cli_local_dir
    if options.dry_run and not Path(discover_dir).is_dir():
        discover_dir = options.source
    discovered = discover_skills(discover_dir)

    include = {sanitize_name(x) for x in options.skill}
    exclude = {sanitize_name(x) for x in options.exclude}
    selected = [s for s in discovered if _should_install_skill(s, include, exclude)]
    if not selected:
        raise ValueError("No skills selected after applying --skill/--exclude filters")

    targets = _resolve_target_agents(options) if options.global_install or options.agent_skills_dir else []

    lock = _load_lockfile(options.lockfile_path)
    lock_skills = lock.setdefault("skills", {})
    if not isinstance(lock_skills, dict):
        lock_skills = {}
        lock["skills"] = lock_skills

    installed: list[dict[str, object]] = []
    for skill in selected:
        skill_folder_name = to_prefixed_folder_name(skill.sanitized_name)
        canonical_path = _install_to_canonical(
            skill,
            options.canonical_dir,
            overwrite=options.overwrite,
            dry_run=options.dry_run,
        )
        target_results: list[dict[str, str]] = []
        for target in targets:
            if target == "custom":
                assert options.agent_skills_dir is not None
                target_dir = options.agent_skills_dir.expanduser()
            else:
                target_dir = Path.home() / AGENT_MAP[target][1]
            mode_used = _install_to_agent_dir(
                canonical_path,
                target_dir,
                skill_folder_name,
                overwrite=options.overwrite,
                dry_run=options.dry_run,
                link_mode=options.link_mode,
            )
            target_results.append(
                {
                    "agent": target,
                    "target_dir": str(target_dir),
                    "mode": mode_used,
                }
            )

        now = _now_iso()
        previous = lock_skills.get(skill_folder_name, {})
        installed_at = previous.get("installedAt", now) if isinstance(previous, dict) else now
        lock_skills[skill_folder_name] = {
            "name": skill.name,
            "sourceType": "local-plugin-copy",
            "sourcePath": str(options.source),
            "cliLocalPath": str(skill.source_dir),
            "canonicalPath": str(canonical_path),
            "installedAt": installed_at,
            "updatedAt": now,
            "hash": _dir_hash(skill.source_dir),
        }
        installed.append(
            {
                "name": skill.name,
                "sanitized_name": skill.sanitized_name,
                "folder_name": skill_folder_name,
                "canonical_path": str(canonical_path),
                "targets": target_results,
            }
        )

    _write_lockfile(options.lockfile_path, lock, dry_run=options.dry_run)
    return {
        "dry_run": options.dry_run,
        "sync": sync_result,
        "selected_skills": [s.sanitized_name for s in selected],
        "selected_skill_folders": [to_prefixed_folder_name(s.sanitized_name) for s in selected],
        "targets": targets,
        "canonical_dir": str(options.canonical_dir),
        "lockfile": str(options.lockfile_path),
        "installed": installed,
        "options": asdict(options),
    }


def run_remove(options: RemoveOptions) -> dict[str, object]:
    selected_skills = {to_prefixed_folder_name(x) for x in options.skill} if options.skill else None
    targets = _resolve_targets(options.agent_skills_dir, options.agent, options.all_agents)

    removed_canonical: list[str] = []
    for entry in _iter_skill_entries(options.canonical_dir, selected_skills):
        removed_canonical.append(entry.name)
        _remove_path(entry, dry_run=options.dry_run)

    removed_targets: list[dict[str, str]] = []
    for target in targets:
        if target == "custom":
            assert options.agent_skills_dir is not None
            target_dir = options.agent_skills_dir.expanduser()
        else:
            target_dir = Path.home() / AGENT_MAP[target][1]
        for entry in _iter_skill_entries(target_dir, selected_skills):
            removed_targets.append({"agent": target, "path": str(entry)})
            _remove_path(entry, dry_run=options.dry_run)

    lock = _load_lockfile(options.lockfile_path)
    lock_skills = lock.get("skills", {})
    if isinstance(lock_skills, dict):
        for skill_name in list(lock_skills.keys()):
            if not str(skill_name).startswith(SKILL_FOLDER_PREFIX):
                continue
            if selected_skills and skill_name not in selected_skills:
                continue
            lock_skills.pop(skill_name, None)
    _write_lockfile(options.lockfile_path, lock, dry_run=options.dry_run)

    return {
        "dry_run": options.dry_run,
        "removed_canonical": removed_canonical,
        "removed_targets": removed_targets,
        "targets": targets,
        "canonical_dir": str(options.canonical_dir),
        "lockfile": str(options.lockfile_path),
    }


def _iter_skill_entries(base_dir: Path, selected_skills: set[str] | None) -> list[Path]:
    if not base_dir.exists():
        return []
    entries: list[Path] = []
    for entry in sorted(base_dir.iterdir()):
        if not entry.is_dir() and not entry.is_symlink():
            continue
        if not entry.name.startswith(SKILL_FOLDER_PREFIX):
            continue
        if selected_skills and entry.name not in selected_skills:
            continue
        entries.append(entry)
    return entries


def _remove_path(entry: Path, *, dry_run: bool) -> None:
    if dry_run:
        return
    if entry.is_symlink() or entry.is_file():
        entry.unlink()
    else:
        shutil.rmtree(entry)


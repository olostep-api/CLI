from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from src.skills_install import InstallOptions, RemoveOptions, discover_skills, run_install, run_remove


def _write_skill(base: Path, name: str, description: str = "desc") -> None:
    skill_dir = base / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n",
        encoding="utf-8",
    )


def test_discover_skills_reads_frontmatter(tmp_path: Path):
    _write_skill(tmp_path, "scrape")
    _write_skill(tmp_path, "search")

    found = discover_skills(tmp_path)
    assert [x.sanitized_name for x in found] == ["scrape", "search"]


def test_run_install_dry_run_selects_skills(tmp_path: Path):
    source = tmp_path / "plugin-skills"
    _write_skill(source, "scrape")
    _write_skill(source, "search")
    options = InstallOptions(
        source=source,
        cli_local_dir=tmp_path / "cli-local",
        canonical_dir=tmp_path / "canonical",
        lockfile_path=tmp_path / ".skill-lock.json",
        agent=[],
        all_agents=False,
        global_install=False,
        agent_skills_dir=tmp_path / "custom-agent-skills",
        skill=["scrape"],
        exclude=[],
        dry_run=True,
        overwrite=True,
        link_mode="auto",
        yes=True,
    )
    result = run_install(options)
    assert result["selected_skills"] == ["scrape"]
    assert result["dry_run"] is True


def test_run_install_unknown_agent_fails(tmp_path: Path):
    source = tmp_path / "plugin-skills"
    _write_skill(source, "scrape")
    options = InstallOptions(
        source=source,
        cli_local_dir=tmp_path / "cli-local",
        canonical_dir=tmp_path / "canonical",
        lockfile_path=tmp_path / ".skill-lock.json",
        agent=["not-real"],
        all_agents=False,
        global_install=True,
        agent_skills_dir=None,
        skill=[],
        exclude=[],
        dry_run=True,
        overwrite=True,
        link_mode="auto",
        yes=False,
    )
    with pytest.raises(ValueError):
        run_install(options)


def test_run_install_writes_lockfile(tmp_path: Path):
    source = tmp_path / "plugin-skills"
    _write_skill(source, "scrape")
    options = InstallOptions(
        source=source,
        cli_local_dir=tmp_path / "cli-local",
        canonical_dir=tmp_path / "canonical",
        lockfile_path=tmp_path / ".skill-lock.json",
        agent=[],
        all_agents=False,
        global_install=False,
        agent_skills_dir=tmp_path / "custom-agent-skills",
        skill=[],
        exclude=[],
        dry_run=False,
        overwrite=True,
        link_mode="copy",
        yes=True,
    )
    run_install(options)
    data = json.loads(options.lockfile_path.read_text(encoding="utf-8"))
    assert data["skills"]["olostep-scrape"]["name"] == "scrape"


def test_run_install_lockfile_uses_real_cli_local_path(tmp_path: Path):
    source = tmp_path / "plugin-skills"
    # Different folder name and frontmatter name to validate lockfile path accuracy.
    _write_skill(source, "scrape-folder")
    skill_md = source / "scrape-folder" / "SKILL.md"
    skill_md.write_text(
        "---\nname: scrape\ndescription: desc\n---\n\n# scrape\n",
        encoding="utf-8",
    )

    options = InstallOptions(
        source=source,
        cli_local_dir=tmp_path / "cli-local",
        canonical_dir=tmp_path / "canonical",
        lockfile_path=tmp_path / ".skill-lock.json",
        agent=[],
        all_agents=False,
        global_install=False,
        agent_skills_dir=tmp_path / "custom-agent-skills",
        skill=[],
        exclude=[],
        dry_run=False,
        overwrite=True,
        link_mode="copy",
        yes=True,
    )
    run_install(options)
    data = json.loads(options.lockfile_path.read_text(encoding="utf-8"))
    assert data["skills"]["olostep-scrape"]["cliLocalPath"].endswith("/cli-local/scrape-folder")


def test_run_install_symlink_mode_uses_absolute_target(tmp_path: Path):
    source = tmp_path / "plugin-skills"
    _write_skill(source, "scrape")
    relative_canonical = Path("relative-canonical")
    options = InstallOptions(
        source=source,
        cli_local_dir=tmp_path / "cli-local",
        canonical_dir=relative_canonical,
        lockfile_path=tmp_path / ".skill-lock.json",
        agent=[],
        all_agents=False,
        global_install=False,
        agent_skills_dir=tmp_path / "custom-agent-skills",
        skill=["scrape"],
        exclude=[],
        dry_run=False,
        overwrite=True,
        link_mode="symlink",
        yes=True,
    )
    cwd = Path.cwd()
    try:
        # Exercise relative canonical dir behavior.
        os.chdir(tmp_path)
        run_install(options)
    finally:
        os.chdir(cwd)

    link_path = (tmp_path / "custom-agent-skills" / "olostep-scrape")
    assert link_path.is_symlink()
    assert Path(os.readlink(link_path)).is_absolute()


def test_run_remove_only_removes_olostep_prefixed(tmp_path: Path):
    canonical = tmp_path / "canonical"
    canonical.mkdir(parents=True, exist_ok=True)
    (canonical / "olostep-scrape").mkdir()
    (canonical / "thirdparty-tool").mkdir()
    lockfile = tmp_path / ".skill-lock.json"
    lockfile.write_text(
        json.dumps(
            {
                "version": 1,
                "skills": {
                    "olostep-scrape": {"name": "scrape"},
                    "thirdparty-tool": {"name": "thirdparty"},
                },
            }
        ),
        encoding="utf-8",
    )
    result = run_remove(
        RemoveOptions(
            canonical_dir=canonical,
            lockfile_path=lockfile,
            agent=[],
            all_agents=False,
            agent_skills_dir=None,
            skill=[],
            dry_run=False,
            yes=True,
        )
    )
    assert result["removed_canonical"] == ["olostep-scrape"]
    assert (canonical / "thirdparty-tool").exists()
    parsed = json.loads(lockfile.read_text(encoding="utf-8"))
    assert "thirdparty-tool" in parsed["skills"]

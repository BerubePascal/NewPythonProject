# Python tools

Personal tooling, used on both the work laptop and at home. Commits here use the
personal identity (Pascal_b@hotmail.com) via an `includeIf` in `~/.gitconfig`.
The user commits and pushes through VS Code's Source Control tab, not the CLI.

- `scaffold_project.py` — scaffolds a new Python project: venv in
  `~/.venvs/<name>` (kept outside OneDrive on purpose), VS Code settings,
  pyproject.toml with an engineering starter set, src layout, editable
  install, optional git init. Templates for the generated files are in
  `templates/*.tmpl` (string.Template, `${name}` placeholders). It installs
  `nicefigures` into each new venv in editable mode from this folder.
- `src/nicefigures/` — installable package (`pyproject.toml` at the root):
  matplotlib helpers for publication-ready figures (thin spines, inward ticks,
  grid, limits snapped to full ticks, 8.8/18 cm widths). Style values live
  only in `src/nicefigures/nice.mplstyle`; the helpers read them from there.
- Tests: `python -m pip install -e ".[test]"` then `python -m pytest`.
  This repo has no venv of its own.

## Decisions (2026-10-15 overhaul; details in git history)

- Venv path must be the same on both machines (`settings.json` is committed
  with `${env:USERPROFILE}\.venvs\<name>`), so venvs are keyed by name, not a
  path hash. Same-name clashes are caught by `<venv>/.project-path`; the user
  passes `--venv-name`.
- `nicefigures` is deliberately not in generated projects' `dependencies`:
  pip would look it up on PyPI (dependency confusion). It is installed
  separately from this folder, so this folder must not move.
- PyTorch is an optional `ml` extra (`--ml`): large, and it has no wheels for
  Python 3.15, the only Python installed on the work laptop as of 2026-10-15.
- `nicefigures.main(fig, ax)` is kept as a deprecated alias of `apply_style`
  for older scripts.
- uv considered and not adopted (extra tool to install on both machines).

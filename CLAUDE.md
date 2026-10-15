# Python tools

Personal tooling, used on both the work laptop and at home. Commits here use the
personal identity (Pascal_b@hotmail.com) via an `includeIf` in `~/.gitconfig`.

- `new_project.py` — scaffolds a new Python project: venv in `~/.venvs/<name>`
  (kept outside OneDrive on purpose), VS Code settings, pyproject.toml, editable
  install, starter files.
- `nicefigures.py` — matplotlib helpers for publication-ready figures (thin
  spines, inward ticks, grid, limits snapped to full ticks, 8.8/18 cm widths).

## Improvement plan (in order)

1. ~~Put the folder under git~~ (done 2026-10-15)
2. Fix `new_project.py` bugs:
   - `subprocess.run` calls lack `check=True`; failures print success anyway
   - venv created with `"python"` from PATH; use `sys.executable` (and
     `sys.version_info` instead of `get_venv_python_version`)
   - pyproject `name` is the OS username; use the normalized folder name
   - venvs keyed by folder basename only; same-named projects share a venv
   - generated `.gitignore` ignores `.vscode/` (the settings it just made) and
     `.venv/` (not where the venv lives)
   - README template says venv is local `.venv`; it is in `~/.venvs/`
   - top-level package named `utils` is too generic; prefer `src/<name>/`
   - minor: editable install runs before README exists; `settings.json` is
     overwritten on rerun; tk root never destroyed; venv path built twice;
     fallback version docstring says 3.10, code returns 3.13; use
     `python -m pip` everywhere instead of a separate pip path helper
   - improvements: argparse with optional path (GUI only as fallback), pathlib,
     templates in files, deps only in pyproject, `git init` + first commit,
     consider uv
3. Clean up `nicefigures.py`:
   - delete dead `get_data_range` and the commented-out old `even_ticks`
   - `_snap_limits`: upper bound lacks the near-spacing check the lower bound
     has; absolute `tol` breaks at small scales — use `np.isclose(x/s, round(x/s))`
   - `even_ticks`: skip non-linear (log) axes
   - `resize_figure`: use `fig.canvas.draw_idle()` not `plt.draw()`; docstring
     says 18.2 cm, code uses 18.0
   - rename `main(fig, ax)` to `apply_style(fig, axes=None)`, loop over all axes
   - move static styling into a `nice.mplstyle` style sheet
4. Package `nicefigures` (with the .mplstyle) so `new_project.py` can install it
   into new venvs; add pytest tests (`_snap_limits`, generated pyproject).

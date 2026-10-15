"""
===============================================================================
scaffold_project.py - New Python project for VS Code
===============================================================================

Description:
    Scaffolds a standardized Python project in a folder and creates its
    virtual environment in ~/.venvs/<venv-name>. The venv lives outside the
    project on purpose, so OneDrive does not sync it.

    Created in the project folder (existing files are kept):
        - src/<package>/__init__.py   importable package (src layout)
        - main.py                     entry point
        - pyproject.toml              metadata and dependencies (starts with
                                      an engineering set: numpy, scipy,
                                      pandas, matplotlib, sympy, scikit-learn…)
        - README.md, .gitignore
        - .vscode/settings.json       points VS Code at the venv (merged)

    The venv is created with the Python running this script. The project is
    installed in it in editable mode with its `dev` extra (ipykernel,
    pytest), together with nicefigures from the folder of this script (also
    editable, so fixes to nicefigures reach every project).

    If the project uses git (asked, unless --git or --no-git is given),
    `git init` is run and the scaffold files are committed. Folders already
    inside a git repository are left as they are.

    File contents come from the templates/ folder next to this script.
    Rerunning on an existing project is safe: files are kept, the venv is
    reused and the project reinstalled.

Usage:
    python scaffold_project.py [PATH] [--venv-name NAME] [--git | --no-git]
                               [--no-nicefigures] [--ml]

    PATH            project folder, created if missing. Without it, a folder
                    picker opens and the git question is asked in a dialog.
    --venv-name     venv folder in ~/.venvs (default: normalized folder name).
                    Needed when another project already uses that name.
    --git/--no-git  answer the git question in advance.
    --no-nicefigures  do not install nicefigures.
    --ml            also install PyTorch (the `ml` extra). PyTorch often lags
                    new Python releases; run this script with a supported
                    Python, e.g. `py -3.13 scaffold_project.py --ml`.

------------------------------------------------------------------------------
Author:     Pascal Berube
Email:      Pascal_b@hotmail.com
Version:    2.0.0
Date:       2026-10-15
License:    MIT License
Python:     3.10+ (tested with 3.15)
Platform:   Windows, Linux, macOS

===============================================================================
Update Log:
===============================================================================
- [2025-07-02] Initial version with full cross-platform support and setup logic
- [2026-10-15] 2.0.0: renamed from new_project.py. Fail on command errors,
               venv from sys.executable, pyproject name from the folder, venv
               ownership check, src/<package> layout, templates in files,
               argparse/pathlib, optional git init + first commit (asked),
               dependencies in pyproject only with an engineering starter
               set and dev/ml extras, nicefigures installed in every venv
===============================================================================
"""

import argparse
import json
import re
import shutil
import string
import subprocess
import sys
import unicodedata
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent  # also the nicefigures package root
TEMPLATES_DIR = TOOLS_DIR / "templates"
VENVS_DIR = Path.home() / ".venvs"

# File inside each venv recording the project it belongs to, so two projects
# with the same folder name do not silently share a venv.
OWNER_FILE = ".project-path"

# Files and folders committed in the first commit of a new repository.
SCAFFOLD_PATHS = [
    ".gitignore",
    ".vscode/settings.json",
    "README.md",
    "main.py",
    "pyproject.toml",
    "src",
]


def run(cmd, **kwargs):
    """
    Run a command, echoing it first, and raise CalledProcessError on failure.

    Args:
        cmd (list): Program and arguments (str or Path).
        **kwargs: Passed to subprocess.run (e.g. cwd).
    """
    cmd = [str(c) for c in cmd]
    print("  $", subprocess.list2cmdline(cmd), flush=True)
    subprocess.run(cmd, check=True, **kwargs)


def choose_directory():
    """
    Open a GUI dialog to let the user select a directory for the new project.

    Returns:
        str: The selected directory, or an empty string if cancelled.
    """
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()  # Hide the main tkinter window
    try:
        return filedialog.askdirectory(title="Select directory for the new project")
    finally:
        root.destroy()


def ask_use_git(gui):
    """
    Ask whether the project should be a git repository or standalone.

    Args:
        gui (bool): Ask in a dialog box instead of the terminal.

    Returns:
        bool: True to initialize a repository.
    """
    question = "Use git for this project (git init + first commit)?"
    if gui:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        try:
            return messagebox.askyesno("New project", question)
        finally:
            root.destroy()

    while True:
        answer = input(f"{question} [Y/n] ").strip().lower()
        if answer in ("", "y", "yes"):
            return True
        if answer in ("n", "no"):
            return False


def normalize_name(folder_name):
    """
    Turn a folder name into a distribution name for pyproject.toml.

    Accents are stripped and every run of other characters becomes a dash:
    "Étude Fatigue_2" -> "etude-fatigue-2".

    Args:
        folder_name (str): The project folder's name.

    Returns:
        str: Lowercase name made of letters, digits and single dashes.
    """
    ascii_name = (
        unicodedata.normalize("NFKD", folder_name).encode("ascii", "ignore").decode()
    )
    return re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-") or "project"


def package_name(dist_name):
    """
    Turn a distribution name into a valid import name: "etude-2" -> "etude_2".

    Args:
        dist_name (str): Name returned by normalize_name.

    Returns:
        str: Python identifier, prefixed with "pkg_" if it starts with a digit.
    """
    name = dist_name.replace("-", "_")
    return f"pkg_{name}" if name[0].isdigit() else name


def venv_python(venv):
    """
    Get the path to the Python interpreter inside a virtual environment.

    Args:
        venv (Path): Root of the virtual environment.

    Returns:
        Path: <venv>/Scripts/python.exe on Windows, <venv>/bin/python elsewhere.
    """
    if sys.platform == "win32":
        return venv / "Scripts" / "python.exe"
    return venv / "bin" / "python"


def write_from_template(dest, template_name, **values):
    """
    Create a file from a template in TEMPLATES_DIR, unless it already exists.

    Placeholders in templates use string.Template syntax: ${name}.

    Args:
        dest (Path): File to create.
        template_name (str): File name inside TEMPLATES_DIR.
        **values: Placeholder values.
    """
    if dest.exists():
        print(f"Kept existing {dest}")
        return
    template = string.Template(
        (TEMPLATES_DIR / template_name).read_text(encoding="utf-8")
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(template.substitute(values), encoding="utf-8")
    print(f"Created {dest}")


def git_config(project_dir, key):
    """
    Read a git config value as git would see it from project_dir.

    Running inside the project folder means `includeIf` rules apply, so the
    identity matches the one the commits will use.

    Returns:
        str: The value, or "" if unset or git is unavailable.
    """
    if shutil.which("git") is None:
        return ""
    result = subprocess.run(
        ["git", "config", "--get", key], cwd=project_dir, capture_output=True, text=True
    )
    return result.stdout.strip()


def authors_line(project_dir):
    """
    Build the pyproject.toml `authors` line from the git identity.

    Returns:
        str: The line with its trailing newline, or "" if no identity is set.
    """
    name = git_config(project_dir, "user.name")
    email = git_config(project_dir, "user.email")
    fields = [f'{key} = "{value}"' for key, value in (("name", name), ("email", email)) if value]
    if not fields:
        return ""
    return f"authors = [{{ {', '.join(fields)} }}]\n"


def create_package(project_dir, package):
    """
    Create src/<package>/__init__.py so the project is importable.

    Args:
        project_dir (Path): Root of the project.
        package (str): Import name of the package.
    """
    init_file = project_dir / "src" / package / "__init__.py"
    if init_file.exists():
        print(f"Kept existing {init_file}")
        return
    init_file.parent.mkdir(parents=True, exist_ok=True)
    init_file.touch()
    print(f"Created {init_file}")


def setup_vscode_settings(project_dir, venv_name):
    """
    Point VS Code at the venv in .vscode/settings.json.

    Existing settings are kept; only the interpreter path is set. The path
    uses ${env:USERPROFILE} / ${env:HOME} so the file works for any user.

    Args:
        project_dir (Path): Root of the project.
        venv_name (str): Folder name of the venv inside ~/.venvs.
    """
    if sys.platform == "win32":
        interpreter = f"${{env:USERPROFILE}}\\.venvs\\{venv_name}\\Scripts\\python.exe"
    else:
        interpreter = f"${{env:HOME}}/.venvs/{venv_name}/bin/python"

    settings_path = project_dir / ".vscode" / "settings.json"
    settings = {}
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            # VS Code allows comments in settings.json; json cannot read those.
            print(
                f"Warning: could not parse {settings_path}; left unchanged.\n"
                f'  Set "python.defaultInterpreterPath": "{interpreter}" yourself.'
            )
            return

    settings["python.defaultInterpreterPath"] = interpreter
    settings.setdefault("python.terminal.activateEnvironment", True)

    settings_path.parent.mkdir(exist_ok=True)
    settings_path.write_text(json.dumps(settings, indent=4) + "\n", encoding="utf-8")
    print(f"Wrote {settings_path}")


def check_venv_owner(venv, project_dir):
    """
    Stop if the venv exists and belongs to another project.

    So two projects with the same folder name never share a venv. A venv
    that records no owner (made by an older version) is accepted.

    Args:
        venv (Path): Where the venv lives.
        project_dir (Path): Root of the project that wants it.
    """
    owner_file = venv / OWNER_FILE
    if not owner_file.exists():
        return
    owner = owner_file.read_text(encoding="utf-8").strip()
    if Path(owner) != project_dir:
        sys.exit(
            f"Error: {venv} belongs to another project: {owner}\n"
            "Rerun with --venv-name to use a different venv, or delete that "
            "venv if the project was moved."
        )


def create_virtualenv(venv, project_dir):
    """
    Create the venv with the interpreter running this script and upgrade pip.

    An existing venv is reused (check_venv_owner has already vetted it).

    Args:
        venv (Path): Where the venv lives.
        project_dir (Path): Root of the project that owns it.
    """
    owner_file = venv / OWNER_FILE
    if venv.exists():
        print(f"Reusing virtual environment {venv}")
    else:
        run([sys.executable, "-m", "venv", venv])
        run([venv_python(venv), "-m", "pip", "install", "--upgrade", "pip"])
        print(f"Created virtual environment {venv}")
    owner_file.write_text(str(project_dir), encoding="utf-8")


def install_project(venv, project_dir, with_nicefigures=True, with_ml=False):
    """
    Install the project in editable mode, with the dependencies in pyproject.toml.

    The `dev` extra (ipykernel, pytest) is always installed; the `ml` extra
    (PyTorch) only on request. nicefigures is installed first, in editable
    mode from TOOLS_DIR. It is not listed in the project's dependencies on
    purpose: pip would then look for a package of that name on PyPI. A legacy
    requirements.txt is also installed if one exists.

    Args:
        venv (Path): The project's venv.
        project_dir (Path): Root of the project.
        with_nicefigures (bool): Also install nicefigures.
        with_ml (bool): Also install the `ml` extra.
    """
    python = venv_python(venv)
    if with_nicefigures:
        run([python, "-m", "pip", "install", "-e", TOOLS_DIR])
    extras = "dev,ml" if with_ml else "dev"
    run([python, "-m", "pip", "install", "-e", f"{project_dir}[{extras}]"])
    requirements = project_dir / "requirements.txt"
    if requirements.exists():
        run([python, "-m", "pip", "install", "-r", requirements])
    print("Installed the project in editable mode.")


def git_toplevel(project_dir):
    """
    Find the git repository that already contains project_dir, if any.

    Returns:
        str: The repository's root, or "" if there is none.
    """
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=project_dir,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def git_init(project_dir):
    """
    Initialize a git repository unless git is missing or one already applies.

    Args:
        project_dir (Path): Root of the project.

    Returns:
        bool: True if a new repository was created.
    """
    if shutil.which("git") is None:
        print("git not found; skipping repository setup.")
        return False
    toplevel = git_toplevel(project_dir)
    if toplevel:
        print(f"Already inside the git repository {toplevel}; skipping git init.")
        return False
    run(["git", "init", "-b", "main"], cwd=project_dir)
    return True


def git_first_commit(project_dir):
    """
    Commit the scaffold files (only those, not whatever else is in the folder).

    Args:
        project_dir (Path): Root of the new repository.
    """
    paths = [p for p in SCAFFOLD_PATHS if (project_dir / p).exists()]
    run(["git", "add", "--", *paths], cwd=project_dir)
    run(["git", "commit", "-m", "Initial project scaffold"], cwd=project_dir)


def setup_python_project(
    project_dir, venv_name=None, use_git=True, with_nicefigures=True, with_ml=False
):
    """
    Run all setup steps for the project in project_dir.

    Files are written first so the editable install sees a complete project;
    the first commit comes last.

    Args:
        project_dir (Path): Absolute path of the project folder.
        venv_name (str, optional): Venv folder name; defaults to the
            normalized project name.
        use_git (bool): Initialize a repository and commit the scaffold.
        with_nicefigures (bool): Install nicefigures in the venv.
        with_ml (bool): Also install the `ml` extra (PyTorch).
    """
    dist_name = normalize_name(project_dir.name)
    package = package_name(dist_name)
    venv_name = venv_name or dist_name
    venv = VENVS_DIR / venv_name
    check_venv_owner(venv, project_dir)

    # Before writing pyproject.toml, so includeIf identities apply to `authors`.
    new_repo = use_git and git_init(project_dir)

    write_from_template(
        project_dir / "pyproject.toml",
        "pyproject.toml.tmpl",
        name=dist_name,
        authors=authors_line(project_dir),
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}",
    )
    write_from_template(
        project_dir / "README.md",
        "README.md.tmpl",
        title=project_dir.name,
        package=package,
        venv_name=venv_name,
    )
    write_from_template(project_dir / "main.py", "main.py.tmpl", package=package)
    write_from_template(project_dir / ".gitignore", "gitignore.tmpl")
    create_package(project_dir, package)
    setup_vscode_settings(project_dir, venv_name)

    create_virtualenv(venv, project_dir)
    install_project(venv, project_dir, with_nicefigures, with_ml)

    if new_repo:
        git_first_commit(project_dir)

    print(f"\nProject setup in {project_dir} is complete.")


def main():
    parser = argparse.ArgumentParser(description="Scaffold a new Python project.")
    parser.add_argument(
        "path",
        nargs="?",
        help="project folder, created if missing (a folder picker opens if omitted)",
    )
    parser.add_argument(
        "--venv-name",
        help="name of the venv folder in ~/.venvs (default: normalized folder name)",
    )
    git_choice = parser.add_mutually_exclusive_group()
    git_choice.add_argument(
        "--git", dest="git", action="store_true", help="git init and first commit"
    )
    git_choice.add_argument(
        "--no-git", dest="git", action="store_false", help="standalone, no git"
    )
    parser.set_defaults(git=None)  # neither flag: ask
    parser.add_argument(
        "--no-nicefigures",
        action="store_true",
        help="do not install nicefigures in the venv",
    )
    parser.add_argument(
        "--ml",
        action="store_true",
        help="also install the ml extra (PyTorch, large download)",
    )
    args = parser.parse_args()

    gui = not args.path
    path = args.path or choose_directory()
    if not path:
        sys.exit("No directory selected. Exiting...")

    project_dir = Path(path).expanduser().resolve()
    project_dir.mkdir(parents=True, exist_ok=True)

    use_git = args.git
    if use_git is None:
        # Only ask when the answer matters; git_init reports the other cases.
        if shutil.which("git") is None or git_toplevel(project_dir):
            use_git = True
        else:
            use_git = ask_use_git(gui)

    try:
        setup_python_project(
            project_dir,
            args.venv_name,
            use_git=use_git,
            with_nicefigures=not args.no_nicefigures,
            with_ml=args.ml,
        )
    except subprocess.CalledProcessError as error:
        sys.exit(
            f"\nSetup failed: {subprocess.list2cmdline(error.cmd)} "
            f"exited with code {error.returncode}."
        )


if __name__ == "__main__":
    main()

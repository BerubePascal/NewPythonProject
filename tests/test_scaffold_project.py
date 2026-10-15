import tomllib

import pytest

import scaffold_project


@pytest.mark.parametrize(
    "folder, dist, package",
    [
        ("MyProject", "myproject", "myproject"),
        ("Étude Fatigue_2", "etude-fatigue-2", "etude_fatigue_2"),
        ("2026 data", "2026-data", "pkg_2026_data"),
        ("--", "project", "project"),
    ],
)
def test_names(folder, dist, package):
    assert scaffold_project.normalize_name(folder) == dist
    assert scaffold_project.package_name(dist) == package


@pytest.mark.parametrize("authors", ["", 'authors = [{ name = "Pascal Bérubé", email = "p@x.com" }]\n'])
def test_generated_pyproject(tmp_path, authors):
    dest = tmp_path / "pyproject.toml"
    scaffold_project.write_from_template(
        dest, "pyproject.toml.tmpl", name="etude-2", authors=authors, python_version="3.13"
    )
    project = tomllib.loads(dest.read_text(encoding="utf-8"))["project"]

    assert project["name"] == "etude-2"
    assert project["requires-python"] == ">=3.13"
    assert {"numpy", "scipy", "pandas", "matplotlib"} <= set(project["dependencies"])
    assert project["optional-dependencies"]["ml"] == ["torch"]
    assert ("authors" in project) == bool(authors)


def test_write_from_template_keeps_existing_file(tmp_path):
    dest = tmp_path / "main.py"
    dest.write_text("mine", encoding="utf-8")
    scaffold_project.write_from_template(dest, "main.py.tmpl", package="x")
    assert dest.read_text(encoding="utf-8") == "mine"


@pytest.mark.parametrize("template", ["README.md.tmpl", "main.py.tmpl", "gitignore.tmpl"])
def test_templates_have_no_stray_placeholders(tmp_path, template):
    scaffold_project.write_from_template(
        tmp_path / "out", template, title="T", package="p", venv_name="v"
    )
    assert "$" not in (tmp_path / "out").read_text(encoding="utf-8")


def test_venv_owner_check(tmp_path):
    venv = tmp_path / "venv"
    venv.mkdir()
    (venv / scaffold_project.OWNER_FILE).write_text(str(tmp_path / "a"), encoding="utf-8")

    scaffold_project.check_venv_owner(venv, tmp_path / "a")  # same project: fine
    with pytest.raises(SystemExit):
        scaffold_project.check_venv_owner(venv, tmp_path / "b")

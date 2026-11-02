import pathlib
import tempfile

import build


def make_course(root):
    course = pathlib.Path(root, "demo-tax")
    (course / "lessons").mkdir(parents=True)
    (course / "AGENTS.md").write_text("# Demo tutor rules\n")
    (course / "facts.md").write_text("# Facts\nRate: 18%\n")
    (course / "lessons/02-second.md").write_text("# Lesson 2\n")
    (course / "lessons/01-first.md").write_text("# Lesson 1\n")
    return course


def test_bundle():
    with tempfile.TemporaryDirectory() as root:
        text = build.bundle(make_course(root), "demo-tax")
    assert text.startswith(build.course_header("demo-tax"))
    assert "https://things-they-dont-teach-you.github.io/demo-tax.md" in text
    assert "PROGRESS CARD" in text
    for part in ["# Demo tutor rules", "Rate: 18%", "# Lesson 1", "# Lesson 2"]:
        assert part in text
    assert text.index("# Lesson 1") < text.index("# Lesson 2")


def test_is_course():
    assert build.is_course({"topics": ["subject-tax", "country-za"], "archived": False})
    assert not build.is_course({"topics": ["subject-tax"], "archived": True})
    assert not build.is_course({"topics": [], "archived": False})
    planned = {"topics": ["subject-tax", "country-gb", "planned"], "archived": False}
    assert not build.is_course(planned)
    assert build.is_planned(planned)
    assert not build.is_planned({"topics": ["subject-tax", "country-za"], "archived": False})


def test_start_page_lists_courses():
    page = build.start_page(
        [{"name": "demo-tax", "description": "Demo", "topics": ["subject-tax", "country-za"]}],
        [{"name": "uk-tax", "topics": ["subject-tax", "country-gb", "planned"]}],
    )
    assert "https://things-they-dont-teach-you.github.io/demo-tax.md" in page
    assert "Demo" in page and "country-za" in page
    ready, planned = page.split("## Planned courses")
    assert "uk-tax" not in ready
    assert "https://github.com/things-they-dont-teach-you/uk-tax" in planned


if __name__ == "__main__":
    test_bundle()
    test_is_course()
    test_start_page_lists_courses()
    print("ok")

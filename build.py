"""Builds the chat editions: start.md, and per course an index plus one page per lesson.

Usage: python3 build.py OUT_DIR
"""
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import urllib.request

ORG = "things-they-dont-teach-you"
SITE = f"https://{ORG}.github.io"
HERE = pathlib.Path(__file__).parent


def course_url(name):
    return f"{SITE}/{name}.md"


def lesson_title(path):
    return path.read_text().splitlines()[0].lstrip("# ").strip()


def facts_for(lesson_text, facts):
    """Keeps only the facts.md sections a lesson names in a <!-- facts: A; B --> line.

    No such line keeps every section; "none" keeps only the intro. An unknown name fails the build,
    so a renamed section can't silently drop a figure a lesson relies on.
    """
    m = re.search(r"<!--\s*facts:\s*(.*?)\s*-->", lesson_text, re.S)
    if not m:
        return facts
    intro, *sections = facts.split("\n## ")
    keep = []
    for want in (w.strip().lower() for w in m.group(1).split(";")):
        if want == "none":
            continue
        found = [sec for sec in sections if sec.lower().startswith(want)]
        if not found:
            raise ValueError(f"facts.md has no section starting {want!r}")
        keep += [sec for sec in found if sec not in keep]
    return "\n\n".join([intro.strip(), *("## " + sec.strip() for sec in keep)]) + "\n"


def course_pages(course_dir, name):
    """Returns {published path: text}: a small index, then one self-contained page per lesson."""
    course_dir = pathlib.Path(course_dir)
    rules = (course_dir / "AGENTS.md").read_text().strip()
    facts = (course_dir / "facts.md").read_text().strip()
    lessons = sorted((course_dir / "lessons").glob("*.md"))
    paths = [f"{name}/{lesson.name}" for lesson in lessons]
    header = (HERE / "chat/lesson-header.md").read_text()

    index = (HERE / "chat/course-index.md").read_text().replace("{course}", name).replace(
        "{lessons}", "\n".join(f"- {lesson_title(l)}: {SITE}/{p}" for l, p in zip(lessons, paths)))
    pages = {f"{name}.md": index, f"{name}/facts.md": facts + "\n"}
    for i, (lesson, path) in enumerate(zip(lessons, paths)):
        last = i == len(lessons) - 1
        next_url = f"{SITE}/{path}" if last else f"{SITE}/{paths[i + 1]}"
        nxt = ("this is the last lesson of the course; congratulate them, and suggest another course "
               f"from {SITE}/start.md") if last else f"{lesson_title(lessons[i + 1])}, at {next_url}"
        top = (header.replace("{course}", name).replace("{title}", lesson_title(lesson))
               .replace("{url}", f"{SITE}/{path}").replace("{next_url}", next_url).replace("{next}", nxt)
               .replace("{facts_url}", f"{SITE}/{name}/facts.md"))
        text = lesson.read_text().strip()
        pages[path] = f"{top}{rules}\n\n---\n\n{facts_for(text, facts).strip()}\n\n---\n\n{text}\n"
    return pages


def has_subject(repo):
    return not repo["archived"] and any(t.startswith("subject-") for t in repo["topics"])


def is_course(repo):
    return has_subject(repo) and "planned" not in repo["topics"]


def is_planned(repo):
    return has_subject(repo) and "planned" in repo["topics"]


def start_page(courses, planned=()):
    lines = [f"- **{c['name']}**: {c['description']} ({', '.join(c['topics'])}). Address: {course_url(c['name'])}" for c in courses]
    planned_lines = [f"- **{p['name']}** ({', '.join(t for t in p['topics'] if t != 'planned')}): https://github.com/{ORG}/{p['name']}" for p in planned]
    return ((HERE / "chat/start.md").read_text()
            .replace("{courses}", "\n".join(lines) or "None yet.")
            .replace("{planned}", "\n".join(planned_lines) or "None."))


def main(out):
    out = pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(f"https://api.github.com/orgs/{ORG}/repos?per_page=100") as r:
        repos = json.load(r)
    courses = [repo for repo in repos if is_course(repo)]
    planned = [repo for repo in repos if is_planned(repo)]
    with tempfile.TemporaryDirectory() as tmp:
        for c in courses:
            dest = pathlib.Path(tmp, c["name"])
            subprocess.run(["git", "clone", "-q", "--depth", "1", c["clone_url"], str(dest)], check=True)
            for path, text in course_pages(dest, c["name"]).items():
                (out / path).parent.mkdir(parents=True, exist_ok=True)
                (out / path).write_text(text)
    (out / "start.md").write_text(start_page(courses, planned))
    print(f"built start.md and {len(courses)} course(s) in {out}")


if __name__ == "__main__":
    main(sys.argv[1])

"""Builds the chat editions: start.md, and one <course>.md per course repository.

Usage: python3 build.py OUT_DIR
"""
import json
import pathlib
import subprocess
import sys
import tempfile
import urllib.request

ORG = "things-they-dont-teach-you"
SITE = f"https://{ORG}.github.io"
HERE = pathlib.Path(__file__).parent


def course_url(name):
    return f"{SITE}/{name}.md"


def course_header(name):
    text = (HERE / "chat/course-header.md").read_text()
    return text.replace("{course}", name).replace("{url}", course_url(name))


def bundle(course_dir, name):
    course_dir = pathlib.Path(course_dir)
    parts = [course_header(name)]
    files = [course_dir / "AGENTS.md", course_dir / "facts.md", *sorted((course_dir / "lessons").glob("*.md"))]
    for f in files:
        parts.append(f"<!-- {f.relative_to(course_dir)} -->\n\n{f.read_text().strip()}\n")
    return "\n".join(parts)


def is_course(repo):
    return not repo["archived"] and any(t.startswith("subject-") for t in repo["topics"])


def start_page(courses):
    lines = [f"- **{c['name']}**: {c['description']} ({', '.join(c['topics'])}). Address: {course_url(c['name'])}" for c in courses]
    return (HERE / "chat/start.md").read_text().replace("{courses}", "\n".join(lines) or "None yet.")


def main(out):
    out = pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(f"https://api.github.com/orgs/{ORG}/repos?per_page=100") as r:
        courses = [repo for repo in json.load(r) if is_course(repo)]
    with tempfile.TemporaryDirectory() as tmp:
        for c in courses:
            dest = pathlib.Path(tmp, c["name"])
            subprocess.run(["git", "clone", "-q", "--depth", "1", c["clone_url"], str(dest)], check=True)
            (out / f"{c['name']}.md").write_text(bundle(dest, c["name"]))
    (out / "start.md").write_text(start_page(courses))
    print(f"built start.md and {len(courses)} course(s) in {out}")


if __name__ == "__main__":
    main(sys.argv[1])

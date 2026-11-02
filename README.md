# Website

Source for [things-they-dont-teach-you.github.io](https://things-they-dont-teach-you.github.io).

The `Build and deploy site` workflow publishes it on every push to `main`, daily, and on demand:

- `index.html` is the home page.
- `build.py` makes the chat editions that learners' AI chat apps read: `start.md` (survey and
  course list, from `chat/start.md`) and one `<course>.md` per course repository (the course's
  `AGENTS.md`, `facts.md` and lessons, after the chat header in `chat/course-header.md`). A course
  is any repository with a `subject-*` topic.
- `python3 test_build.py` checks the build. Run `python3 build.py out/` to see the output locally.

The contact form posts to [Formspree](https://formspree.io); its form id is in the `action`
attribute. When adding a course, add a card to the Courses section.

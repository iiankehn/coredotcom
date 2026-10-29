@../brain/CORE.md

# CORE website (core.iiankehn.com)

Static tech publication: plain HTML, one CSS file and a tiny JavaScript file.
No framework, package manager or build step. GitHub Pages deploys `main`.
Shared CORE context is imported above from the `brain` repo; if it is missing,
ask the user to clone `iiankehn/brain` beside this repo.

`BUILD_NOTES.md` is the authoritative design, structure and publishing guide.
Read it before changing pages.

## Commands

```bash
python3 tools/check_site.py         # check posts new or changed since origin/main (run before every push)
python3 tools/check_site.py --all   # audit the whole site (older posts have known drift)
python3 -m http.server 8000         # preview at http://localhost:8000
```

## Rules

- Fixed dark Metro design, teal accent `#64d8c8`. No light mode or theme toggle.
- Never rename existing post files; URLs are permanent. Preserve `CNAME`.
- Every story is original writing that credits its source, separates rumor from
  confirmed news, and is dated by the source's publication date.
- Featured art: WebP, exactly 1672 × 941, shared by the card and the article.
- After any stylesheet change, bump the `style.css?v=` string on every page and the template.
- Commit messages: plain sentence such as "Publish three October 23 CORE stories".

## Skills

- `core-story`: research, write and publish one or more stories end to end.

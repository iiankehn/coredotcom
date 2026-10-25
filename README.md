# CORE by Iian Kehn

CORE is a static publication covering phones, computers, operating systems, software, and services. It is written in plain HTML and one CSS file, with a small vanilla JavaScript file for menu behavior; there is no framework, package manager, database, or build step.

The site uses a fixed dark theme inspired by Microsoft Metro: large lightweight type, flat surfaces, generous spacing, and a teal accent. There is no light mode.

Live site: https://core.iiankehn.com

## What is included

- `index.html` — blog homepage; every story card is written by hand
- `about.html` — About page
- `posts/*.html` — individual articles, each a complete page
- `templates/post-template.html` — starting point for a new article
- `css/style.css` — all layout, typography, color, and responsive rules
- `js/main.js` — accessible mobile-menu behavior; exits early on pages without menu controls, which currently includes all of them
- `js/theme.js` — placeholder comment noting the fixed dark theme; not loaded by any page
- `assets/images/` — WebP featured artwork, 1672 × 941
- `BUILD_NOTES.md` — structure, publishing, and deployment details
- `tools/check_site.py` — optional standard-library checker for the publishing rules; nothing to install
- `CNAME` — GitHub Pages custom domain

## Run locally

From the repository root:

```bash
python3 -m http.server 8000
```

Then visit `http://localhost:8000`.

## Publish a new post

1. Copy `templates/post-template.html` into `posts/` with a short lowercase filename, such as `posts/my-new-post.html`.
2. Replace the title, meta description, category and field-note number, headline, deck, date, reading time, body, and end-note number.
3. Add the featured image figure and the “Original reporting” credit. The template doesn't include them; copy them from a recent post.
4. Add a matching `.project.has-image` card to `index.html` in date order, newest first.
5. Preview the homepage and the post, then commit to `main`.

See `BUILD_NOTES.md` for the full checklist.

## Deployment

GitHub Pages serves the site from `main`, root `/`. Pushing to `main` publishes it. Any other static host works too, with no build command.

## Design changes

Colors and sizing values are custom properties under `:root` at the top of `css/style.css`. When changing the stylesheet, also bump its `?v=` query string in every page so browsers fetch the new version.

## License and content

Site code may be adapted for personal use. Written content remains © Iian Kehn unless stated otherwise.

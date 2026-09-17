# CORE by Iian Kehn

CORE is a lightweight static publishing site built with readable HTML and CSS. One small vanilla JavaScript file controls the mobile menu; there is no framework, package manager, database, or build step.

## What is included

- `index.html` — blog homepage
- `about.html` — editable about-page template
- `templates/post-template.html` — clean starting point for new posts
- `css/style.css` — all layout, typography, color, and responsive rules
- `js/main.js` — accessible mobile-menu behavior
- `assets/images/` — optimized WebP featured artwork for published reports
- `BUILD_NOTES.md` — editing and deployment instructions
- `CNAME` — GitHub Pages custom domain configuration

## Run locally

You can open `index.html` directly in a browser. For a closer match to a production server, run any static file server from the project directory, for example:

```bash
python3 -m http.server 8000
```

Then visit `http://localhost:8000`.

## Publish a new post

1. Copy `templates/post-template.html` into `posts/`.
2. Give the copy a short lowercase filename, such as `posts/my-new-post.html`.
3. Replace the placeholder title, description, date, note number, reading time, and article text.
4. Copy the post entry in `index.html`, update its metadata and links, and place it above older entries.
5. Preview the homepage and the post before uploading or committing your changes.

## Deployment

Upload the project exactly as-is to any static host or ordinary web server. GitHub Pages, Cloudflare Pages, Netlify, Apache, and Nginx can all serve it without a build command. Point the web root at this directory and make `index.html` the default document.

## Design changes

The main color and sizing values are grouped at the top of `css/style.css` under `:root`. Change those custom properties to adjust the site without searching through the rest of the stylesheet.

## License and content

Site code may be adapted for personal use. Written content remains © Iian Kehn unless stated otherwise.

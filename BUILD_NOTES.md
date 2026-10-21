# Build Notes

## Project goals

CORE is a durable, server-independent publication. It uses semantic HTML, one human-readable CSS file, and a small dependency-free JavaScript file. There is nothing to install, compile, or update.

## Visual design

The site is a modern interpretation of Microsoft Metro with a fixed dark presentation. It shares its design language with Iian's other sites, using a CORE-specific accent.

| Token | Value | Use |
| --- | --- | --- |
| `--bg` | `#101010` | Page background |
| `--surface` | `#1c1c1c` | Cards and raised surfaces |
| `--text` | `#f5f5f5` | Body text |
| `--muted` | `#b0b0b0` | Secondary text |
| `--line` | `#383838` | Dividers |
| `--accent` | `#64d8c8` | Links, focus rings, highlights |
| `--accent-hover` | `#9de8dd` | Link hover |

The font stack begins with Segoe UI Variable and Segoe UI, then falls back to platform fonts. Every page declares `color-scheme: dark` and `theme-color` `#101010`. There is no light mode or theme toggle; don't reintroduce one without a deliberate design decision.

## Page structure

Every page contains the same three regions:

1. A header with the CORE wordmark and Blog and About links shown directly; there is no collapsed menu.
2. A unique `<main>` region for the page content.
3. A compact footer.

**Homepage.** `.page-heading` introduces the blog, followed by `section.projects`, a grid of story cards. Each card is an `article.project.has-image` containing:

- a decorative `.tile-image` background (`alt=""`, `aria-hidden="true"`), with `loading="lazy"` on every card except the first
- a `.tag` holding the `<time>` and reading time
- an `h3` headline link
- a one-sentence summary that matches the article's deck
- a `.project-link` “Read report” link

**Articles.** These use `.page-heading` with `.back-link` and `.overline` (`Category · Field note NNN`), then the `h1`, `.article-deck`, and `.byline`. Next come `figure.article-image`, the `.reading` body (`.standfirst` for the opening paragraph and `h2` section headings), an `aside.reading` source credit, and `footer.reading` with the end-note number.

**About page.** It uses `.page-heading` and `.reading`.

## Paths

Root pages reference `css/…`, `js/…`, and `assets/…`. Pages in `posts/` use `../css/…`, `../assets/…`, and `../index.html`. Every page has an explicit `.html` URL, so don't rename existing files.

## Adding posts

1. Copy `templates/post-template.html` into `posts/`. Never edit the template as the live post.
2. Use the next unused field-note number; check the highest existing one with `grep -ho 'Field note [0-9]*' posts/*.html | sort | tail -1`. Use it in both the overline and the end note.
3. Date the post by the original source's publication date. Use `<time datetime="YYYY-MM-DD">` with a matching readable date.
4. Add the featured figure after the header. The template doesn't include it:
   `<figure class="article-image"><img src="../assets/images/NAME.webp" alt="Meaningful description" width="1672" height="941"></figure>`
5. Add the source credit before the end note: an `aside.reading` with `<strong>Original reporting</strong>`, links to the reporting and any official confirmation, and an image credit.
6. Add the matching card to `index.html` in date order, newest first. Update the URL in both the headline and “Read report” links. Keep the headline, summary, date, reading time, and image identical between the card and the article. Give the previous first card `loading="lazy"`.

### Editorial defaults

- Approved recurring sources: The Verge, Thurrott, AppleInsider, 9to5Mac, 9to5Google, Windows Central, and Apple Newsroom. Confirm claims with an official primary source where one exists. A one-off source used for a single story does not join this list.
- Check existing posts before picking a story to avoid duplicate coverage.
- Write original headlines and copy, separate rumor from confirmed news, and credit the original reporting.
- Every post needs relevant featured artwork, also used on its card. Use official press images where they're appropriate and permitted; otherwise use original, colorful artwork specific to the story. Save images as optimized WebP files at 1672 × 941.

## Styling map

- `:root` — color tokens
- `.site-header`, `.brand`, `.header-inner nav` — shared header
- `.page-heading`, `.overline`, `.back-link` — page titles
- `.projects`, `.project`, `.project.has-image`, `.tile-image`, `.tag`, `.project-link` — homepage cards
- `.article-deck`, `.byline`, `.article-image`, `.reading`, `.standfirst` — articles
- `.site-footer` — shared footer

**Breakpoints.** Media queries at `800px` and `600px` handle tablet and phone, with a small `360px` adjustment. There are also reduced-motion and print rules.

**Metadata separators.** `.byline` and `article > footer.reading` use flex wrapping, with a `> * + *::before` rule inserting the middle-dot separators. This handles any mix of `span` and `time` elements; don't add separators by hand.

**Cache-busting.** Pages load `css/style.css?v=story-separators-20261013`. After changing the stylesheet, update that version string in `index.html`, `about.html`, every file in `posts/`, and the template.

## Accessibility

- Semantic landmarks and heading order support assistive technology.
- A skip link appears when it receives keyboard focus.
- Focus states use a 2px accent outline (`:focus-visible`).
- Text uses relative units, and layouts tolerate 200% text enlargement.
- `prefers-reduced-motion` disables transitions and the card image hover effect.
- The current page is marked with `aria-current="page"`, not color alone.
- Article images have meaningful alt text; homepage card images are decorative because the card text identifies the story.
- `js/main.js` supports `aria-expanded`, Escape, outside clicks, focus return, and closing at desktop widths when `.menu-toggle` and `.mobile-nav` markup is present.

## Deployment

No build command is required.

### GitHub Pages

Deploys from `main`, root `/`. The `CNAME` file keeps the custom domain `core.iiankehn.com`, and DNS is managed through Cloudflare. After pushing, the “pages build and deployment” workflow publishes the site, usually within a minute.

### Other hosts

Serve the repository root as a static directory, with `index.html` as the default document. No rewrites are needed.

## Pre-publish checklist

- Open the homepage, the About page, and every new post.
- Test at phone, tablet, and desktop widths, and confirm there is no horizontal scrolling.
- Check relative links and image loading from both root pages and `posts/`.
- Verify titles, meta descriptions, dates, reading times, credits, and field-note numbers.
- Confirm the card and the article match, and that the cards are in date order.
- Keep `CNAME` while the custom domain is in use.

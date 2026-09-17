# Build Notes

## Project goals

CORE was rebuilt as a durable, server-independent publication. The implementation deliberately uses only semantic HTML and one human-readable CSS file. There is no JavaScript and nothing to install, compile, or update.

## Page structure

Every page contains the same three broad regions:

1. A header with the CORE wordmark and two navigation links.
2. A unique `<main>` region for the page content.
3. A compact footer with ownership and implementation details.

The homepage uses an archive row for every post. Individual articles use the `.article-layout` and `.prose` classes. The About page combines `.page-layout` with the same `.prose` treatment so long-form text remains consistent.

## Adding posts safely

Copy `templates/post-template.html`; never edit the template as the live post. The template is already one directory below the project root, so its `../` asset and navigation paths are correct for files placed in `posts/`.

After writing the post, add a matching `<article class="post-row">` block to `index.html`. Check the filename in both the headline link and the “Read essay” link.

Use ISO dates in the `<time datetime="YYYY-MM-DD">` attribute and natural-language dates for visible text. Update the field-note number in the post and archive number on the homepage.

## Styling map

- `:root` — colors, fonts, maximum widths
- `.site-header`, `.brand`, `nav` — shared navigation
- `.intro`, `.archive`, `.post-row` — homepage
- `.page-layout`, `.about-copy` — About page
- `.article-*`, `.prose`, `blockquote` — single posts
- `.site-footer` — shared footer
- media queries — tablet and mobile adjustments

The responsive breakpoints are `48rem` and `30rem`. The layout also uses `clamp()` so type and spacing scale smoothly between phone and desktop sizes.

## Accessibility decisions

- Semantic landmarks and heading order support navigation by assistive technology.
- A keyboard-visible skip link appears when focused.
- Focus states use a high-contrast blue outline.
- Text sizes use relative units and layouts tolerate 200% text enlargement.
- `prefers-reduced-motion` disables nonessential transition duration.
- Color is never the only way the current page is identified.

## Deployment notes

No build command is required. Deploy the repository root as a static directory.

### GitHub Pages

In repository settings, choose **Deploy from a branch**, select `main`, and choose `/ (root)`. The included `CNAME` retains the custom domain `core.iiankehn.com`.

### Apache or Nginx

Copy all files and directories to the configured document root. Ensure directory indexes include `index.html`. No rewrites are required because every page has an explicit `.html` URL.

### Other static hosts

Select the repository root as the publish directory. Leave the build command empty.

## Pre-publish checklist

- Open the homepage, About page, and every new post.
- Test at phone, tablet, and desktop widths.
- Confirm there is no horizontal scrolling.
- Check all relative links from both root pages and `posts/` pages.
- Update page titles and meta descriptions.
- Confirm the post appears in the homepage archive.
- Keep `CNAME` if the GitHub Pages custom domain is still in use.

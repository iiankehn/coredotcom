---
name: core-story
description: Research, write and publish CORE news stories ("field notes") on core.iiankehn.com — pick non-duplicate stories from approved sources, write original copy, create 1672×941 WebP artwork, add the post and homepage card, and validate with tools/check_site.py. Use for "publish a story", "today's CORE batch", or "write about <news>".
---

# Publish CORE stories

`BUILD_NOTES.md` is authoritative. This skill is the order of work. Where the
notes and the latest published posts differ in markup (for example the source
credit is now `<strong>Sources</strong>` with an "Independently written from
reporting by ..." line), match the latest posts.

## 1. Pick stories

- Approved recurring sources: The Verge, Thurrott, AppleInsider, 9to5Mac,
  9to5Google, Windows Central, Apple Newsroom. Confirm claims with an official
  primary source where one exists.
- Search for coverage first: `grep -il "<keyword>" posts/*.html`. Skip stories
  already covered unless there is genuinely new information.
- Batches are usually two or three stories. Propose the list with one-line
  angles to the user before writing, unless they already chose.

## 2. Write each post

1. Copy `templates/post-template.html` to `posts/<descriptive-slug>.html`.
2. Next field-note number:
   `grep -ho 'Field note [0-9]*' posts/*.html | sort -t' ' -k3 -n | tail -1`, plus one.
   Use it in the overline (`Category · Field note NNN`) and `End note NNN`.
3. Date with the source's publication date (`<time datetime="YYYY-MM-DD">`).
4. Title, `meta description`, deck, byline (`By Iian Kehn`), reading time
   (about 200 words per minute, minimum 1).
5. Body: an opening paragraph that states the news, then context and why it
   matters. Original sentences only, no copied phrasing. Attribute reports
   ("9to5Mac reports ..."), and label rumors as rumors.
6. Sources aside: link the original reporting (with the author's name) and any
   official confirmation, plus the image credit.

## 3. Artwork

- Official press images only when appropriate and permitted; credit them.
- Otherwise create original, colorful artwork specific to the story. Generate
  it with Pillow (`python3`) or ImageMagick (`convert`), or use art the user
  supplies. The caption reads "Concept illustration created for CORE."
- Save it as `assets/images/<slug>.webp`, exactly 1672 × 941, optimized
  (around 100 to 150 KB). Write meaningful alt text on the article image.

## 4. Homepage card

Add an `article.project.has-image` card to `index.html` in date order, newest
first. The headline, summary (identical to the deck), date, reading time and
image match the article. Only the first card omits `loading="lazy"`; add it to
the card that used to be first.

## 5. Validate and publish

- `python3 tools/check_site.py` must report 0 errors.
- Preview with `python3 -m http.server 8000` at phone and desktop widths if a
  browser is available.
- Commit ("Publish <topics> stories") on the working branch. Pushing to `main`
  publishes immediately, so only do that when the user asks.

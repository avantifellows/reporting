---
name: generate-pdf
description: How report PDFs are generated and how to debug them (?format=pdf, debug mode, CSS/image inlining).
triggers:
  - "pdf"
  - "format=pdf"
  - "print version"
edges:
  - target: context/architecture.md
    condition: for the external HTML-to-PDF service's place in the flow
  - target: patterns/add-report-endpoint.md
    condition: when wiring PDF support into a new endpoint
last_updated: 2026-07-09
---

# Generate / Debug PDFs

## Context

`app/utils/pdf_converter.py` exposes `convert_template_to_pdf(template_response, debug=False)`. Every report endpoint routes through it when `?format=pdf`. It rewrites the rendered HTML with BeautifulSoup — inlines `app/static/style.css` into a `<style>` tag (falling back to a hard-coded default CSS block), converts local `<img>` srcs to base64 data URIs — then POSTs `{"html": ...}` to `HTML_TO_PDF_SERVER_URL` and streams the PDF back.

## Steps

1. Make sure the endpoint follows the standard contract (`format`/`debug` params → `convert_template_to_pdf`).
2. For v2 student reports, PDF uses the print template (`student_quiz_report_v2_print.html`); `?print=true` previews it as HTML in the browser.
3. Check output first with `?format=pdf&debug=true` — this returns the exact inlined HTML the PDF service would receive, no service call needed.
4. Only then test the real PDF with `HTML_TO_PDF_SERVER_URL` set.

## Gotchas

- Only the style.css link is inlined — a `<link>` to any other stylesheet silently won't apply in the PDF (the link tag stays but the service can't fetch relative URLs).
- Remote images (http/https/data:) are left as-is; local images must exist under `app/static/` to be base64-inlined.
- The SAM parameter is named `HtmlToPdfUrl` but the runtime env var is `HTML_TO_PDF_SERVER_URL` — keep both in sync when changing the service URL.
- Failure returns an HTML "Error generating PDF" page with status 500, not an exception — check Lambda logs for the service's status/text.

## Verify

- [ ] `?format=pdf&debug=true` shows CSS inside `<style>` and images as `data:` URIs
- [ ] Real PDF renders with styling and images
- [ ] Non-PDF path (`format` omitted) unaffected

## Debug

- Unstyled PDF → CSS didn't inline; confirm the template links the stylesheet at the "/static/style.css" URL and the file exists relative to the working dir
- Broken images → image not under `app/static/`; check converter's printed path attempts in logs
- 500 page → PDF service down/unreachable; hit `HTML_TO_PDF_SERVER_URL` directly with a minimal HTML payload

## Update Scaffold

- [ ] Update this file if the converter's search paths or service contract change

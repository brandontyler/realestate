# PDF Generation Research (2026-03-10)

**Bead:** bd-2ql
**Goal:** Find or build a PDF generation skill for kiro-cli that produces slick, professional CMA reports.

## Options Evaluated

### 1. weasyprint (Python, HTML→PDF) ⭐ RECOMMENDED

- Pure Python, excellent CSS support (flexbox, grid, `@page` rules, headers/footers, page numbers)
- ~8k GitHub stars, widely used, actively maintained
- The model writes HTML/CSS naturally — weasyprint just renders it
- Supports print-quality features: page breaks, widows/orphans, bleed, crop marks
- No JavaScript (no dynamic charts) — but we can pre-render charts as images or use CSS-only visualizations
- Requires system deps: `pango`, `cairo`, `gdk-pixbuf` (one-time install)
- **Verdict: Best fit.** Lightest weight, model-native workflow, print-quality output.

### 2. Playwright/Puppeteer (headless Chrome → PDF)

- Full browser rendering with JavaScript support (Chart.js, D3, etc.)
- Pixel-perfect but heavy — requires Chromium (~300MB)
- We already have Playwright via the `dev-browser` skill if we ever need it
- Slow startup, overkill for document generation
- **Verdict: Overkill.** Already available via dev-browser for one-off needs.

### 3. FabianGenell/pdf-mcp-server (MCP, Node.js)

- MCP native, built-in themes (professional/minimal/dark), markdown→PDF
- Image embedding, TOC generation, custom styles, template system
- Only 3 GitHub stars, 14 commits, single contributor
- MCP server (user prefers skills), Node.js dependency, Playwright under the hood
- **Verdict: Too new, too few users, wrong delivery mechanism.**

### 4. reportlab (Python, programmatic PDF)

- Pure Python, no system deps, very mature (~3.5k stars)
- Programmatic API — you build PDFs with code, not HTML/CSS
- Painful for complex layouts; the model would write reportlab code instead of HTML
- Good for simple invoices, bad for rich reports with photos and maps
- **Verdict: Wrong abstraction.** HTML/CSS is what the model naturally produces.

### 5. Peedief (SaaS MCP)

- Beautiful output, template system, "AI-first" marketing
- SaaS with pricing (5 free, then paid), external dependency
- 23 Product Hunt followers, MCP not skill
- **Verdict: No.** Don't want external SaaS for core functionality.

### 6. ms-office-suite skill (jawhnycooke/claude-plugins)

- Comprehensive PDF manipulation (read, create, merge, split, OCR, watermark)
- Uses reportlab for creation — programmatic, not HTML-based
- More about PDF manipulation than beautiful report generation
- Good reference for the skill pattern though
- **Verdict: Good reference, wrong tool for beautiful reports.**

## Recommendation: weasyprint skill

The model already knows HTML/CSS. weasyprint converts it to PDF with excellent print support. The skill teaches the model:

1. How to use weasyprint (`from weasyprint import HTML; HTML(string=html).write_pdf('out.pdf')`)
2. CSS `@page` rules for margins, headers, footers, page numbers
3. Print-specific CSS (`page-break-before`, `widows`, `orphans`)
4. Image embedding (base64 data URIs or file paths)
5. A CMA report HTML/CSS template as a starting point

No MCP server, no Node.js, no Chromium. Just `pip install weasyprint`, write HTML, render PDF. The model does the creative work (layout, design, narrative), weasyprint renders it.

## Why This Fits the "Model Does the Thinking" Philosophy

- The model writes the HTML/CSS for each report — every CMA is custom
- No rigid template engine or report builder constraining the output
- The model can adapt layout based on how many comps there are, what data is available, market conditions
- weasyprint is just the renderer — a tool, not a framework

## Next Steps

1. Install weasyprint + system deps
2. Build `~/.kiro/skills/pdf-report/SKILL.md` teaching the model weasyprint patterns
3. Create a base CMA HTML/CSS template the model can customize
4. Test with real ACTRIS data

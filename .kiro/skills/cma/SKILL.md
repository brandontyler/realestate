---
name: cma
description: Comparative Market Analysis workflow for real estate. Use when users ask for a CMA, property valuation, pricing opinion, comps, "what's this house worth", "generate CMA", "run comps", or any request to estimate a property's market value. Also triggers on listing presentation prep or pricing strategy discussions.
---

# CMA Skill — Comparative Market Analysis

A CMA estimates a property's market value by comparing it to similar recently sold properties, then adjusting for differences. This skill defines the workflow, quality standards, and report structure. The model does all the reasoning — no hardcoded formulas.

## Workflow

### Step 1: Identify the Subject Property

Look up the property in MLS by address. Collect:
- Address, beds, baths, sqft, lot size, year built, garage, pool
- Property type/subtype (SFR, condo, townhouse)
- Subdivision name, school district
- Current status (active, closed, off-market)
- Photos (primary photo for report cover)
- Public remarks, features, condition clues

If the property isn't in MLS (e.g., owner considering selling), ask the user for: address, beds, baths, sqft, year built, lot size, notable features.

### Step 2: Pull Sold Comps

Search for closed sales similar to the subject. Start tight, widen if needed:

**Tight search first:**
- Same subdivision OR same zip code
- Same property type
- ±10% sqft (ideal), up to ±20% (acceptable)
- ±1 bedroom
- Sold within 3 months (ideal), up to 6 months (acceptable)

**Widen if fewer than 3 comps:**
- Expand to same city
- ±20-25% sqft
- Up to 9-12 months
- Adjacent zip codes

**Target: 3-6 sold comps.** Fewer than 3 is unreliable. More than 6 dilutes the analysis.

### Step 3: Pull Active Listings (Competition)

Query active listings with similar criteria. This shows what the subject competes against RIGHT NOW. Note:
- How many similar homes are on the market
- Their price range and days on market
- Whether the market is saturated or thin

### Step 4: Pull Pending/Under Contract

Query pending and ActiveUnderContract listings. These are the most current market signal — what buyers are willing to pay TODAY. We won't know contract price, but list price + DOM tells a story.

### Step 5: Analyze and Reason

This is where the model thinks. For each sold comp, consider:

**Comp quality** — How similar is it really?
- Location hierarchy: same subdivision > same school zone > same zip. A comp across a major highway or in a different school attendance zone is a weaker comp even if geographically close.
- Same subdivision = strong comp
- Same property type = required (never comp a condo against a SFR)
- Within 10% sqft = strong, 10-20% = acceptable, >20% = weak
- Within 5 years built = strong, 5-15 = acceptable, >15 = weak
- Sold within 3 months = strong, 3-6 = acceptable, >6 = weak
- Fewer adjustments needed = more reliable comp

**Adjustments** — Always adjust the COMP, never the subject.
- Comp inferior to subject → adjust comp price UP
- Comp superior to subject → adjust comp price DOWN
- Derive adjustment values from the data when possible ($/sqft from the comp set)
- Flag if total adjustments exceed 15-25% of comp's sale price (reduces reliability)

**Red flags to watch for:**
- Distressed sales (foreclosure, short sale, REO) — flag or exclude
- Seller concessions that inflate close price
- Flips (bought and sold within 12 months) — may not reflect typical market
- Comps with excessive DOM (>90 days) — may have been overpriced
- $/sqft outlier: if a comp's $/sqft deviates >20% from the group median, explain why or drop it — it's likely not truly comparable

**Market context:**
- Absorption rate: closed sales last 6 months ÷ 6 = monthly rate. Active listings ÷ monthly rate = months of supply. <3 = seller's market, 3-6 = balanced, >6 = buyer's market.
- Price trend: are recent sales trending up, down, or flat vs. 6 months ago?
- List-to-sale ratio: avg(sale price / list price) — shows negotiation reality

### Step 6: Determine Price Range

From the adjusted comp prices, provide:
- **Low estimate** — lowest adjusted comp price (conservative)
- **Suggested list price** — weighted toward comps needing fewest adjustments
- **High estimate** — highest adjusted comp price (aggressive)
- **Price per sqft range** for context

Weight comps that required fewer adjustments more heavily. A comp needing $5K in adjustments is more reliable than one needing $50K. Also weight more recent sales more heavily — a comp from last month is a stronger signal than one from 5 months ago.

### Step 7: Generate PDF Report (AUTOMATIC)

This step is NOT optional — always generate the PDF.

**IMPORTANT: Use the two-step file-based approach from the pdf-report skill.**
1. Use the `write` tool to create `/tmp/cma_{address_slug}.html` with the full report HTML
2. Run `python3 -c "from weasyprint import HTML; HTML('/tmp/cma_{address_slug}.html').write_pdf('/tmp/cma_{address_slug}.pdf'); print('Done')"` to render

**NEVER embed the HTML inline in a Python string or shell command** — it will
exceed output token limits in ACP/Discord sessions and silently fail.

**Report sections:**

1. **Cover page** — Property photo as hero image (full-width, from MLS Media), address, date, prepared by
2. **Subject property summary** — Key stats, features
3. **Market snapshot** — Months of supply, trend, active count, avg DOM
4. **Sold comps table** — Address, sale price, date, beds/baths/sqft, key differences
5. **Adjustment grid** — Show adjustments per comp and adjusted prices
6. **Active competition** — What's on the market now
7. **Pending sales** — Most current market signal
8. **Price recommendation** — Range with reasoning
9. **Narrative** — Plain-English explanation of the analysis a seller can understand

**Design principles — the report should look like a real estate brochure, not a slide deck:**

- Cover page: property photo is the star. Use the primary MLS photo as a large hero image (full-width or near full-width). Address in clean, simple typography below or overlaid on the photo with a subtle dark scrim. No gradients, no colored boxes, no centered-text-on-solid-background layouts. White or very light background. Date and agent name small at the bottom.
- Use the property photo URL directly from MLS Media (`MediaURL`) in an `<img>` tag — weasyprint fetches remote URLs.
- Typography: use system fonts (Georgia or serif for headings, sans-serif for body). Clean hierarchy — don't over-style.
- Color: one accent color max, used sparingly (table headers, thin rules). Mostly black text on white.
- Tables: clean and readable. Light borders, no heavy colored headers. Zebra striping optional.
- Whitespace: generous margins and padding. Let the data breathe.
- No decorative elements that don't convey information.

**Cover photo selection:** Don't blindly use the first MLS photo. The Media array is already in the subject property response — scan the `ShortDescription` and `Order` fields to pick a better hero image if photo #1 looks like a construction or low-quality shot. Photos 2–5 are often strong interior shots. No extra API calls needed — just pick a different URL from the data you already have.

**Page flow — no half-empty pages:**
- Pack related sections together. Comps table, adjustment grid, active competition, and pending commentary should flow continuously — don't force page breaks between them.
- Only use explicit page breaks before major new sections (cover → content, content → price recommendation).
- If a section has just a few lines of text (e.g., "no pending sales"), keep it with the previous section — never give it its own page.
- The report should be tight: aim for 4–5 pages total (cover + 3–4 content pages). Every page should be at least 70% filled.
- The narrative/analysis and disclaimer should fit on the same page as the price recommendation if possible.

### Step 8: Upload to S3 & Return Presigned URL (AUTOMATIC)

This step is NOT optional — always upload and return the link.

1. Save PDF to `/tmp/cma_{address_slug}.pdf`
2. Upload to S3 bucket `re-agent-reports-035405309532` (us-east-1)
   - Key: `cma/{YYYY-MM-DD}/cma_{address_slug}_{HHmmss}.pdf`
   - Content-Type: `application/pdf`
3. Generate a presigned GET URL with 7-day expiry (604800 seconds)
4. Present the URL to the user

## Chat Output Rules

Do NOT dump the full analysis as text in chat. Keep it brief. The detail goes in the PDF.

In chat, only show:
- Subject property (address, beds/baths/sqft, one line)
- Number of sold comps used
- **Price recommendation** (low / suggested / high)
- Months of supply / market type (one line)
- The presigned S3 link to the full PDF report

Everything else (comp details, adjustments, narratives, competition) belongs in the PDF only.

## Quality Checklist

Before presenting results, verify:
- [ ] At least 3 sold comps (ideally 4-6)
- [ ] All comps are same property type as subject
- [ ] No comp has >25% total adjustments relative to its sale price
- [ ] Active competition included
- [ ] Pending/under contract included
- [ ] Absorption rate / months of supply calculated
- [ ] Distressed sales flagged or excluded
- [ ] Price range provided (not just a single number)
- [ ] Reasoning explained for comp selection and weighting

## Texas-Specific Notes

- Texas is a NON-DISCLOSURE state — sale prices are NOT in public records. MLS is the only reliable source.
- Tax assessed values in Texas lag significantly behind market values. Don't rely on them for pricing.
- Note in report: "Sale price data sourced from MLS. Texas is a non-disclosure state."

## What a CMA is NOT

- Not an appraisal (no USPAP standards, no legal standing for lending)
- Not a guarantee of sale price
- Not based on what the seller "needs" — it's based on what the market says
- Active listings are NOT comps — they haven't been tested by the market. Include them as competition context only.

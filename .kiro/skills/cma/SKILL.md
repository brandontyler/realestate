---
name: cma
description: Comparative Market Analysis workflow for real estate. Use when users ask for a CMA, property valuation, pricing opinion, comps, "what's this house worth", "generate CMA", "run comps", or any request to estimate a property's market value. Also triggers on listing presentation prep or pricing strategy discussions.
---

# CMA Skill — Comparative Market Analysis

The model does all the reasoning — no hardcoded formulas.

## Workflow

### Step 1: Identify the Subject Property

Look up in MLS by address. Collect: address, beds, baths, sqft, lot size, year built, garage, pool, property type/subtype, subdivision, school district, status, photos, remarks.

If not in MLS, ask user for basics.

### Step 2: Pull Sold Comps

Start tight, widen if fewer than 3:

**Tight:** Same subdivision or zip, same property type, ±10% sqft, ±1 bed, sold within 3 months.

**Wider:** Same city, ±20-25% sqft, up to 9-12 months, adjacent zips.

Target 3-6 sold comps.

### Step 3: Pull Active Listings (Competition)

Similar criteria, active status. Note count, price range, DOM.

### Step 4: Pull Pending/Under Contract

Most current market signal — list price + DOM tells a story even without contract price.

### Step 5: Analyze and Reason

For each sold comp, consider:

**Comp quality:**
- Location: same subdivision > same school zone > same zip. Different school attendance zone = weaker comp.
- Same property type required. Within 10% sqft = strong, 10-20% = acceptable. Within 5 years built = strong.
- Fewer adjustments = more reliable.

**Adjustments** — always adjust the COMP, not the subject. Derive values from the data when possible. Flag if total adjustments exceed 15-25% of comp's sale price.

**Red flags:** Distressed sales, seller concessions, flips (<12 months), excessive DOM (>90 days), $/sqft outliers (>20% from group median).

**Market context:**
- Absorption rate: closed last 6mo ÷ 6 = monthly rate. Active ÷ monthly = months of supply. <3 seller's, 3-6 balanced, >6 buyer's.
- Price trend direction
- List-to-sale ratio: avg(sale price / list price)

### Step 6: Determine Price Range

From adjusted comp prices:
- **Low estimate** — lowest adjusted comp (conservative)
- **Suggested list price** — weighted toward comps needing fewest adjustments and most recent sales
- **High estimate** — highest adjusted comp (aggressive)
- **Price per sqft range** for context

### Step 7: Generate PDF Report

Always generate the PDF using the two-step file-based approach from the pdf-report skill:
1. Write HTML to `/tmp/cma_{address_slug}.html` using the file write tool
2. Render: `python3 -c "from weasyprint import HTML; HTML('/tmp/cma_{address_slug}.html').write_pdf('/tmp/cma_{address_slug}.pdf'); print('Done')"`

Do not embed HTML inline in a Python string or shell command — it exceeds output token limits.

**Report sections:** Cover page (hero photo from MLS Media), subject summary, market snapshot, sold comps table, adjustment grid, active competition, pending sales, price recommendation, narrative.

**Design:** Property photo as hero image, clean typography (Georgia/serif headings, sans-serif body), one accent color max, generous whitespace, no decorative elements. Aim for 4-5 pages total, every page 70%+ filled.

**Cover photo:** Scan Media array `ShortDescription` and `Order` fields — don't blindly use photo #1.

### Step 8: Upload to S3 & Return Presigned URL

Always upload after generating:
1. Upload to `re-agent-reports-035405309532` (us-east-1), key: `cma/{YYYY-MM-DD}/cma_{address_slug}_{HHmmss}.pdf`
2. Presigned GET URL with 7-day expiry (604800 seconds)

## Chat Output Rules

Keep chat brief. Detail goes in the PDF. Only show:
- Subject property (one line)
- Number of sold comps used
- Price recommendation (low / suggested / high)
- Months of supply / market type (one line)
- Presigned S3 link

## Quality Checklist

- [ ] At least 3 sold comps, same property type
- [ ] No comp with >25% total adjustments
- [ ] Active competition and pending/UC included
- [ ] Absorption rate calculated
- [ ] Distressed sales flagged or excluded
- [ ] Price range provided with reasoning

## Texas Notes

- Non-disclosure state — MLS is the only reliable sale price source. Note in report.
- Tax assessed values lag significantly — don't rely on them for pricing.

---
name: net-sheet
description: Calculate estimated seller proceeds from a home sale. Use when users ask about net sheets, seller proceeds, closing costs for selling, "what will I walk away with", or "what does the seller net". Trigger phrases include "net sheet", "seller net", "seller proceeds", "what will I walk away with", "closing costs for selling", "what do I net on", or any request to estimate what a seller keeps after a sale.
---

# Seller Net Sheet Calculator

Estimate what a seller walks away with after commissions, closing costs, taxes, and payoffs.

## Inputs

Required: sale price (accept multiple for comparison: "net sheet for 425k, 450k, 475k")

Optional with defaults:
- Listing agent commission: 3%
- Buyer agent commission: 3%
- Mortgage payoff: excluded if unknown
- Repair credits: $0
- Home warranty: $0
- Closing date: 30 days out (for tax proration)
- Property address: to pull tax data from MLS

## Texas-Specific Costs

### Owner's Title Insurance (state-regulated, same everywhere in TX)
| Liability Range | Rate per $1,000 |
|----------------|----------------|
| $0–$100K | $5.75 |
| $100K–$1M | $5.00 |
| $1M–$5M | $2.50 |
| $5M–$15M | $2.25 |
| $15M+ | $2.00 |

Rates are cumulative/tiered (first $100K at $5.75, next $900K at $5.00, etc.)

### Other TX seller costs
- Title/escrow fees: ~$1,800
- Recording fees: ~$50
- Transfer tax: $0 (Texas has none)
- Property tax proration: assessed_value × county_rate ÷ 365 × days_owned_this_year
- Seller customarily pays owner's title policy in TX

### County property tax rates (approximate)
Travis ~1.8%, Williamson ~2.1%, Hays ~1.9%, Collin ~1.8%, Denton ~1.9%, Tarrant ~2.1%, Dallas ~2.0%

If address provided, pull TaxAssessedValue from MLS for proration. Otherwise estimate from sale price (TX assessed values lag market, so use ~85% of sale price as rough assessed value).

## Output

Show a clean itemized table. If multiple prices requested, show side-by-side comparison.

Include disclaimer: *This is an estimate. Actual costs may vary. Consult your title company for exact figures.*

If user asks for a PDF, use the pdf-report skill to generate a one-page net sheet.

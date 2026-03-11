---
name: listing-writer
description: Generate MLS listing descriptions, social media captions, and email copy from property data. Use when users ask to write listing remarks, MLS descriptions, social posts, or marketing copy for a property. Trigger phrases include "write listing for", "listing remarks", "MLS description", "social post for", "write remarks", "listing copy", "describe this property", or any request to write marketing text for a real estate listing.
---

# Listing Description Writer

Generate publish-ready MLS remarks, social media captions, and email blast copy from MLS property data.

## Workflow

1. Pull property data using the MLS skill (address, structure, features, remarks, media)
2. If not in MLS, ask the user for basics: address, beds, baths, sqft, year built, notable features
3. Generate all outputs below

## Outputs

### MLS Remarks — two versions
- **Short (≤500 chars):** For NTREIS and syndication. Every word earns its place.
- **Full (500–1000 chars):** For agent websites and brochures.

Lead with the strongest differentiator — not beds/baths/sqft (already in MLS fields). Be specific and concrete. No filler words ("nice," "great," "beautiful," "must see"). End with a soft CTA.

### Social Media Caption
Under 300 chars before hashtags. Hook in the first line (pattern interrupt — question, bold claim, or punchy fragment). Separate Instagram (lifestyle) and Facebook (detail + link) versions. 3–5 hashtags.

### Email Blast
2–3 paragraphs, narrative style. Weave stats in naturally. Two subject line options (A/B: curiosity vs. feature-driven). End with CTA.

### Tone (optional)
User can request: luxury, investor, first-time-buyer, downsizer. Default: general.

## Fair Housing Compliance (MANDATORY)

Describe the PROPERTY, never who should live there. Use "primary" not "master" for bedrooms/suites/baths. Don't reference protected classes (race, color, religion, national origin, sex, familial status, disability) directly or through implication.

Non-obvious traps to avoid:
- "walking distance to [house of worship]" — religious preference
- "safe/quiet neighborhood" — implies other areas aren't, can be discriminatory
- "exclusive" or "prestigious" — can imply exclusion
- "no children" / "adults only" — familial status (unless verified 55+)

Include at the bottom: *Fair Housing compliant. Describes property features only.*

## North Texas Context (Production Market)

Primary market is DFW via NTREIS. Things the model wouldn't know from MLS data alone:

- School districts are the #1 differentiator in Frisco, Prosper, Southlake, Allen, McKinney, Celina
- Major employer corridor along 121/DNT: Toyota HQ (Plano), Charles Schwab (Westlake), Liberty Mutual, JPMorgan Chase — mention for relocation appeal
- Known master-planned communities: Light Farms, Phillips Creek Ranch, Harvest, Windsong Ranch, Star Trail, Trinity Falls, Union Park
- Local landmarks buyers reference: Legacy West, The Star, Grandscape, Stonebriar
- Storm shelters/safe rooms are a genuine selling point (tornado alley)
- 0.3+ acre lots are premium in DFW master-planned communities (0.2 is standard)
- DFW hashtags: #DFWRealEstate #NorthTexasHomes #FriscoTX #ProsperTX #PlanoTX etc.

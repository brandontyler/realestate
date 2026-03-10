# AI CMA Generator — Research & Build Plan

**Bead:** bd-2mb.1
**Status:** Research complete, awaiting Trestle credentials
**Last updated:** 2026-03-05

---

## 1. What Is a CMA?

A Comparative Market Analysis (CMA) is the report a listing agent prepares for a seller to recommend a list price. It pulls recent sold properties ("comps") that are similar to the subject property, adjusts for differences, and derives a price range. Every listing appointment requires one. Agents currently spend 1-3 hours per CMA manually.

## 2. Trestle API Research

### 2.1 What Is Trestle?

Trestle (by Cotality, formerly CoreLogic) is a real estate data distribution platform. It aggregates and normalizes MLS data from 90+ MLOs across North America into RESO Data Dictionary format. Data is accessed via OData-based WebAPI.

- **Base URL:** `https://api.cotality.com` (migrating from `api-prod.corelogic.com` — use new URL)
- **Auth:** OAuth2 Client Credentials → `POST /trestle/oidc/connect/token`
- **Token lifetime:** 8 hours (cache and reuse)
- **Data standard:** RESO Data Dictionary 1.7 (Platinum Certified)
- **Response format:** JSON (OData), metadata is XML

### 2.2 Authentication

```
POST https://api.cotality.com/trestle/oidc/connect/token
Content-Type: application/x-www-form-urlencoded

client_id=<ID>&client_secret=<SECRET>&grant_type=client_credentials&scope=api
```

Returns `{ "access_token": "...", "expires_in": 28800, "token_type": "Bearer" }`

### 2.3 Rate Limits

| Quota | Baseline |
|-------|----------|
| WebAPI queries/hour | 7,200 |
| WebAPI queries/minute | 180 (burst) |
| Media URL requests/hour | 18,000 |
| Media URL requests/minute | 480 |

Quota info returned in response headers: `Minute-Quota-Limit`, `Hour-Quota-Limit`, `Hour-Quota-ResetTime`.

429 = quota exceeded. Check `Hour-Quota-Available` — if non-zero, you're hitting per-minute limit.

### 2.4 CRITICAL: Feed Type Determines Data Access

| Feed Type | Active Listings | Sold/Closed Listings | Notes |
|-----------|----------------|---------------------|-------|
| IDX | ✅ | ❌ | **Cannot build CMA** |
| IDX Plus | ✅ | ✅ (some) | **Minimum for CMA** |
| VOW | ✅ | ✅ | Good |
| Broker | ✅ | ✅ | Full access |

**Action item:** When credentials arrive, immediately test `StandardStatus eq 'Closed'`. If 404 or empty, need to upgrade feed type.

### 2.5 Property Resource — Key Fields for CMA

Endpoint: `GET /trestle/odata/Property`

**Identity & Address:**
- `ListingKey` (unique ID — use this, not ListingId)
- `ListingId` (agent-facing ID, not guaranteed unique across MLSs)
- `UnparsedAddress`, `City`, `PostalCode`, `StateOrProvince`
- `SubdivisionName`, `CountyOrParish`
- `Latitude`, `Longitude` (for distance calculations)

**Status & Pricing:**
- `StandardStatus` — enum: Active, ActiveUnderContract, Canceled, Closed, Expired, Pending, Withdrawn
- `MlsStatus` — local status (maps to StandardStatus)
- `ListPrice` — current asking price
- `OriginalListPrice` — initial asking price
- `ClosePrice` — actual sale price (only on Closed)
- `CloseDate` — date of sale
- `PreviousListPrice` — last price before current

**Structure:**
- `BedroomsTotal` (Int32)
- `BathroomsTotalInteger` (Int32 — simple count, e.g. 3 for 2 full + 1 half)
- `BathroomsFull`, `BathroomsHalf` (for detailed breakdown)
- `LivingArea` (Decimal 14.2 — total livable sqft)
- `LotSizeSquareFeet` (Decimal 14.2)
- `LotSizeAcres` (Decimal 16.4)
- `YearBuilt` (Int32)
- `YearBuiltEffective` (Int32 — year of major renovation)
- `Stories` (Int32)
- `RoomsTotal` (Int32)

**Parking:**
- `GarageSpaces` (Decimal 14.2)
- `GarageYN` (Boolean)
- `CarportSpaces`, `OpenParkingSpaces`

**Features:**
- `PoolPrivateYN` (Boolean)
- `PoolFeatures` (multi-select)
- `PropertyType` — enum: Residential, Land, Commercial, etc.
- `PropertySubType` — enum: SingleFamilyResidence, Condominium, Townhouse, etc.
- `PropertyCondition` (multi-select)
- `Roof`, `Heating`, `Cooling`, `Fireplace`
- `PropertyAttachedYN` (Boolean)

**Tax & Assessment:**
- `TaxAnnualAmount` (Decimal)
- `TaxAssessedValue` (Int32)
- `TaxYear` (Int32)

**Market Timing:**
- `DaysOnMarket`, `CumulativeDaysOnMarket`
- `OnMarketTimestamp`
- `OriginalEntryTimestamp`
- `PriceChangeTimestamp`

**Descriptions:**
- `PublicRemarks` (up to 12,000 chars — listing description)
- `PrivateRemarks` (agent-only, 4,000 chars)

### 2.6 OData Query Reference

**Filter operators:**
- `eq`, `ne`, `gt`, `ge`, `lt`, `le`
- `and`, `or`, `not`
- `has` (multi-select enum: `Appliances has 'Dishwasher'`)
- `in` (value list: `StandardStatus in ('Active', 'Pending')`)
- `contains()`, `startswith()`, `endswith()` (strings)

**Pagination:**
- `$top=1000` (max per query, default 10)
- `$skip=1000` (offset)
- `@odata.nextLink` returned for auto-pagination

**Other:**
- `$select=Field1,Field2` — limit returned fields
- `$orderby=CloseDate desc`
- `$count=true` — returns `@odata.count` with total
- `$expand=Media($select=MediaURL;$top=1;$orderby=Order)` — inline related data
- `$apply=groupby((PostalCity))` — unique values (max 10,000)
- `PrettyEnums=true` — human-readable enum values (e.g. "Active Under Contract" vs "ActiveUnderContract")

**InKeyIndex fields** (can query up to 300,000 at a time):
`ListingId`, `ListingKey`, `ModificationTimestamp`, `PhotosChangeTimestamp`, `PhotosCount`, `PostalCode`, `StandardStatus`

### 2.7 Media Resource

- `GET /trestle/odata/Media?$filter=ResourceRecordKey eq '<ListingKey>'&$orderby=Order`
- Returns `MediaURL` — direct URL to download image
- Or use `$expand=Media($select=MediaURL;$top=1;$orderby=Order)` on Property query for primary photo inline

### 2.8 Related Resources

| Resource | Use |
|----------|-----|
| Property | Listings (active + sold) |
| Media | Photos |
| Member | Agent info |
| Office | Brokerage info |
| OpenHouse | Open house schedules |
| PropertyRooms | Room-level detail |
| CustomProperty | MLS-specific non-standard fields |

### 2.9 Trestle Pricing

Per-connection monthly fee based on total contracts across Trestle:

| Tier | Contracts | RESO Feed | Direct Feed |
|------|-----------|-----------|-------------|
| Small | ≤50 | $100/mo | $125/mo |
| Medium | 51-100 | $110/mo | $160/mo |
| Large | 101-500 | $125/mo | $200/mo |

Plus MLO license fee (varies by market, charged monthly/quarterly/annually).

---

## 3. CMA Generator Architecture

### 3.1 User Flow

```
Agent: "Run a CMA for 4521 Elm Creek Dr, Plano TX 75024"
  ↓
AI: Looks up subject property in Trestle
  ↓
AI: "Found it — 4 bed, 3 bath, 2,100 sqft, built 2005. Running comps..."
  ↓
AI: Queries sold comps (tiered search)
  ↓
AI: Ranks and selects top 3-6 comps
  ↓
AI: Calculates adjustments per comp
  ↓
AI: Generates price range + narrative
  ↓
AI: Returns summary + downloadable report
  ↓
Agent: Can refine (add/remove comps, adjust values)
```

### 3.2 Comp Search Strategy (Tiered)

**Tier 1 — Tight (try first):**
- Same subdivision OR same zip code
- Same property type/subtype
- ±20% living area sqft
- ±1 bedroom
- Closed in last 6 months

```
$filter=StandardStatus eq 'Closed'
  and PropertyType eq 'Residential'
  and PostalCode eq '75024'
  and BedroomsTotal ge 3 and BedroomsTotal le 5
  and LivingArea ge 1680 and LivingArea le 2520
  and CloseDate ge 2025-09-05
&$select=ListingKey,UnparsedAddress,ClosePrice,CloseDate,ListPrice,
  BedroomsTotal,BathroomsTotalInteger,LivingArea,LotSizeSquareFeet,
  YearBuilt,GarageSpaces,PoolPrivateYN,PropertySubType,
  DaysOnMarket,Latitude,Longitude,SubdivisionName
&$orderby=CloseDate desc
&$top=50
```

**Tier 2 — Wider (if <3 comps from Tier 1):**
- Same city
- ±25% sqft, ±1 bed/bath
- Closed in last 9 months

**Tier 3 — Widest (if still <3):**
- Adjacent zip codes / broader North Texas region (coverage area: DFW metro north through Gainesville/Cooke County)
- ±30% sqft
- Closed in last 12 months

Target: 3-6 best comps.

### 3.3 Comp Ranking Algorithm

Score each potential comp on similarity to subject:

| Factor | Weight | Calculation |
|--------|--------|-------------|
| Distance | 25% | Haversine from lat/long, closer = higher score |
| Sqft difference | 20% | % difference in LivingArea |
| Bed/bath match | 15% | Exact match bonus, penalty per difference |
| Year built proximity | 10% | Absolute year difference |
| Recency of sale | 15% | Days since CloseDate, more recent = higher |
| Same subdivision | 15% | Binary bonus if SubdivisionName matches |

Sort by composite score, select top 3-6.

### 3.4 Adjustment Calculations

For each comp, calculate adjustments vs. subject:

| Factor | Method |
|--------|--------|
| Square footage | (Subject sqft - Comp sqft) × local $/sqft |
| Bedrooms | ±$5K-$15K per bedroom (market-configurable) |
| Bathrooms | ±$5K-$10K per bathroom |
| Garage spaces | ±$5K-$15K per space |
| Pool | ±$15K-$30K |
| Year built | ±$1K-$3K per year difference |
| Lot size | Proportional to local $/sqft of land |
| Condition | Qualitative (if data available) |

Adjusted comp price = `ClosePrice + net adjustments`

### 3.5 Price Determination

From adjusted comp prices:
- **Low estimate:** Lowest adjusted comp price
- **Suggested list price:** Weighted average (favor most similar comps)
- **High estimate:** Highest adjusted comp price
- **Price/sqft range**
- **Avg days on market** for comp set
- **List-to-close ratio:** `avg(ClosePrice / ListPrice)` — shows negotiation reality

### 3.6 Report Output

- Subject property details + primary photo
- Comp table: address, close price, close date, beds/baths/sqft, adjustments, adjusted price
- Map with subject + comp locations (lat/long)
- Price range visualization
- Market stats (DOM, list-to-sale ratio, price/sqft trends)
- AI narrative summary
- Formats: PDF (client-ready), JSON (programmatic)

---

## 4. Build Phases

### Phase 1: Trestle API Client
- OAuth2 auth with token caching
- OData query builder for Property endpoint
- Media URL fetching
- Error handling (429 rate limit, 504 timeout, retry logic)

### Phase 2: Comp Selection Engine
- Subject property lookup by address
- Tiered comp search queries
- Comp ranking/scoring algorithm
- Distance calculation (haversine)

### Phase 3: Price Analysis
- Adjustment calculations per comp
- Price range determination
- Market stats aggregation
- List-to-close ratio analysis

### Phase 4: Report Generation
- AI narrative generation
- HTML template → PDF report
- Comp table formatting
- Map visualization (lat/long)

### Phase 5: Agent Interface
- Conversational input ("Run CMA for [address]")
- Interactive refinement (add/remove comps, override adjustments)
- Report regeneration

---

## 5. Tech Stack

| Component | Choice | Why |
|-----------|--------|-----|
| Language | Python | Fast prototyping, matches Trestle docs |
| HTTP/Auth | `requests` + `oauthlib` | Trestle docs use these exactly |
| Data | `pandas` | Comp analysis, adjustments |
| Distance | `haversine` lib | Lat/long distance |
| Reports | `jinja2` + `weasyprint` | HTML → PDF |
| AI narrative | LLM (agent) | Written analysis |
| Config | `.env` | Credentials, market adjustments |

---

## 6. First Steps When Credentials Arrive

1. **Test auth:**
   ```
   POST https://api.cotality.com/trestle/oidc/connect/token
   ```

2. **Check feed type — can you see sold data?**
   ```
   GET /trestle/odata/Property?$filter=StandardStatus eq 'Closed'
     &$select=ListingKey,ClosePrice,CloseDate&$top=5
   ```
   If empty/404 → need IDX Plus or higher feed.

3. **Check what North Texas data is available:**
   ```
   GET /trestle/odata/Property?$filter=PostalCode eq '75024'
     &$count=true&$top=1
   ```

4. **Read metadata to confirm available fields:**
   ```
   GET /trestle/odata/$metadata
   ```

5. **Pull a sample closed listing with all CMA fields:**
   ```
   GET /trestle/odata/Property?$filter=StandardStatus eq 'Closed'
     and PostalCode eq '75024'
     &$select=ListingKey,UnparsedAddress,ClosePrice,CloseDate,ListPrice,
       BedroomsTotal,BathroomsTotalInteger,LivingArea,LotSizeSquareFeet,
       YearBuilt,GarageSpaces,PoolPrivateYN,PropertySubType,
       Latitude,Longitude,SubdivisionName,DaysOnMarket,
       TaxAnnualAmount,TaxAssessedValue,PublicRemarks
     &$expand=Media($select=MediaURL;$top=1;$orderby=Order)
     &$top=3&$orderby=CloseDate desc
   ```

---

## 7. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| IDX feed (no sold data) | **Blocker** — can't build CMA | Verify feed type immediately; upgrade if needed |
| North Texas MLS not on Trestle | **Blocker** | NTREIS (North Texas) is on Trestle — confirmed via Trestle MLS list |
| Rate limits too low | Medium | 7,200/hr is plenty for CMA (needs ~5-10 queries per CMA) |
| Missing fields (null data) | Medium | Build fallbacks; some MLSs don't populate all fields |
| Adjustment values wrong for market | Medium | Make all adjustment values configurable; let agent override |
| Lat/long missing on some listings | Low | Fall back to zip code distance; use PostalCode matching |

---

## 8. North Texas Market Context (Updated 2026-03-06)

Key stats to calibrate CMA defaults:
- Texas median sale price: ~$339K (up 6.5% YoY per Houzeo)
- Zillow avg TX home value: $294,807 (down 2.4% YoY)
- Avg days on market in North Texas: ~58 days (up slightly)
- Sellers receiving avg 93.7% of original list price
- Statewide DOM essentially flat at ~117 days for new construction
- Inventory rising — 9 months of supply statewide (shifting toward buyer's market)
- 1 in 5 TX sellers had to drop price in 2025 (Realtor.com)

These numbers should inform default adjustment values and market narrative generation.

## 9. Industry Validation (2026 Research)

- 65% of real estate agencies now using AI-powered tools for lead management and engagement (Creole Studios / industry reports)
- AI valuation models reducing pricing errors vs traditional appraisals
- AI lease abstraction tools hitting 99%+ accuracy (V7 Labs / Forbes)
- Flipsnack and others building MLS-to-brochure AI tools via RESO Web API — validates demand for automated MLS data consumption
- WAV Group: brokerages organizing tech by product category (CRM, CMA, website) are missing the strategic picture — need lifecycle-oriented tools

## 10. Open Questions (Updated 2026-03-10)

1. ~~What specific MLS?~~ **NTREIS** — confirmed on Trestle ✅
2. ~~Will the Trestle account be under the broker's license or a tech provider account?~~ **Emailed broker to ask about direct NTREIS credentials** ✅
3. ~~What feed type was requested?~~ **IDX Plus selected on Trestle, but not activated yet ($500 setup). Waiting on broker response re: direct NTREIS access** ✅
4. ~~Target demo area?~~ **All of North Texas, especially north through Gainesville** ✅
5. Active listing analysis (absorption rate, competing inventory)? **TBD — decide after core CMA works**

## 11. Bridge Interactive API — Dev/Test Environment (Added 2026-03-10)

### Why Bridge?
Building against free Austin (ACTRIS) data while waiting for NTREIS access. Both use RESO Data Dictionary, so code is portable.

### Key Differences: Bridge vs Trestle

| Aspect | Trestle | Bridge (ACTRIS ref) |
|--------|---------|---------------------|
| Base URL | `https://api.cotality.com/trestle/odata/` | `https://api.bridgedataoutput.com/api/v2/OData/actris_ref/` |
| Auth | OAuth2 client credentials → bearer token | Static server token → bearer token |
| Token endpoint | `POST {base}/oidc/connect/token` | N/A — token is static |
| Resource name | `Property` | `Property` (singular for abor_ref/actris_ref) |
| Pagination default | 10 per page, max 1000 via `$top` | 10 per page, max 200 via `$top` |
| `$top` behavior | Page size | Page size (v2) or total collection size (v3) |
| Geo search | Use `Latitude`/`Longitude` fields | `geo.distance(Coordinates, POINT(lng lat))` supported |
| Dataset in URL | No (single dataset per credential) | Yes — dataset code in URL path (e.g., `actris_ref`) |
| Enum filtering | `StandardStatus eq 'Closed'` | Same |
| Media | `$expand=Media(...)` or separate Media resource | `$expand=Media(...)` or separate Media resource |

### Bridge API Endpoint Patterns (ACTRIS Reference Server)

```
# Metadata
GET /api/v2/OData/actris_ref/$metadata

# DataSystem info
GET /api/v2/OData/DataSystem('actris_ref')

# Property queries (same OData as Trestle, just different base URL)
GET /api/v2/OData/actris_ref/Property?$filter=...&$select=...&$top=...

# Single property by key
GET /api/v2/OData/actris_ref/Property('listing_key_here')

# Member queries
GET /api/v2/OData/actris_ref/Member?$filter=...

# Geo search (radius in miles from a point)
GET /api/v2/OData/actris_ref/Property?$filter=geo.distance(Coordinates, POINT(-97.62669 30.430726)) le 10&$top=10
```

### Auth Header
```
Authorization: Bearer <BRIDGE_API_TOKEN>
```
No OAuth2 flow needed — the server token from the Bridge dashboard is used directly as a bearer token.

### Provider-Agnostic Architecture

The API client must abstract these differences:
1. **Base URL** — env var `MLS_API_URL`
2. **Auth method** — Trestle: OAuth2 client credentials; Bridge: static bearer token
3. **Dataset path** — Trestle: none; Bridge: dataset code in URL
4. **Pagination limits** — Trestle: max 1000; Bridge v2: max 200

All OData query syntax ($filter, $select, $orderby, $expand, $count) is identical.

### ACTRIS Reference Server Notes
- Contains previous year's Austin MLS data
- Free for development/testing
- RESO Web API certified
- Same RESO Data Dictionary fields as NTREIS
- Includes sold/closed listings (critical for CMA development)
- Supports geo.distance() for radius searches
- Dataset code: likely `actris_ref` (confirmed from RESO examples using `abor_ref` — may be either)

## 12. Gaps & Corrections Identified (2026-03-10 Deep Review)

### 12.1 Rate Limiting — Must Be Baked Into Everything

This is non-negotiable. Every API call must go through a rate limiter.

**Trestle rate limits:**
- 7,200 queries/hour (= 120/min sustained), 180/min burst
- 18,000 media URL requests/hour, 480/min burst
- Response headers: `Minute-Quota-Limit`, `Hour-Quota-Limit`, `Hour-Quota-ResetTime`
- 429 = quota exceeded; check `Hour-Quota-Available` to distinguish hourly vs per-minute limit

**Bridge rate limits:**
- Hourly limit varies by account/dataset (check response headers on first call)
- Burst limit: 1/15 of hourly limit per minute
- Response headers: `Burst-RateLimit-Limit`, `Burst-RateLimit-Remaining`, `Burst-RateLimit-Reset`
- Also has hourly headers (standard)

**Rate limiter requirements for our API client:**
1. Token bucket or sliding window — configurable per provider
2. Read rate limit headers from EVERY response and adjust dynamically
3. On 429: exponential backoff with jitter (start 1s, max 60s, max 3 retries)
4. Pre-request check: if remaining quota is low, sleep until reset
5. Log every API call with timestamp, endpoint, response code, quota remaining
6. Per-CMA budget: a single CMA should use ~4-8 API calls max:
   - 1 call: subject property lookup
   - 1-3 calls: comp search (tiered, stop when enough found)
   - 0-1 calls: media/photos (use $expand to inline, avoid separate calls)
   - 1 call: active competition snapshot
   - 1 call: pending/under contract snapshot
   At 8 calls per CMA, we can safely run ~900 CMAs/hour on Trestle, ~15/min burst
7. Never paginate unnecessarily — use tight $filter + $select to minimize result sets
8. Cache subject property lookups (same property may be queried multiple times during refinement)

### 12.2 Missing from CMA: Active Listings & Pending Sales

The current plan only looks at sold comps. A real CMA also needs:

**Active competition** — What's currently on the market that the subject will compete against?
- Query: `StandardStatus eq 'Active'` with same filters as comp search
- Shows the seller: "Here's what buyers can choose from right now"
- If 15 similar homes are active, pricing needs to be aggressive
- If only 2 are active, seller has leverage

**Pending/under contract** — Properties that went under contract but haven't closed yet
- Query: `StandardStatus in ('Pending', 'ActiveUnderContract')`
- Most current market signal — shows what buyers are willing to pay RIGHT NOW
- We don't know the contract price, but we know the list price and DOM
- A property that went pending in 3 days at full ask = strong market signal

**Absorption rate** — How fast is inventory moving?
- Formula: closed sales in last 6 months ÷ 6 = monthly absorption
- Current active listings ÷ monthly absorption = months of supply
- <3 months = seller's market, 3-6 = balanced, >6 = buyer's market
- This single number tells the broker more about pricing strategy than anything else

### 12.3 Missing: Texas Is a Non-Disclosure State

Critical and previously overlooked. Texas does NOT require sale prices in public records.
- County assessor records won't show sale prices
- The MLS is the ONLY reliable source of sold data in Texas
- This makes our MLS connection even more valuable
- Can't cross-reference with public records easily
- Tax assessed values in Texas lag significantly behind market values
- Our CMA report should note this: "Sale price data sourced from MLS; Texas is a non-disclosure state"

### 12.4 Missing: Seller Concessions Distort Close Price

`ClosePrice` may not reflect true transaction value. If seller paid $10K toward buyer's closing costs, the recorded close price is inflated.
- RESO fields to check: `Concessions`, `ConcessionsAmount`, `ConcessionsComments`
- Not all MLSs populate these consistently
- Adjustment engine should flag comps where concession data is available and adjust
- At minimum, note in report when concession data is unavailable
- Fannie Mae caps: 3% for >90% LTV, 6% for 75-90% LTV, 9% for ≤75% LTV

### 12.5 Missing: Distressed Sales Filtering

Foreclosures and short sales sell below market value — shouldn't be weighted equally.
- RESO fields: `SpecialListingConditions` (may contain 'ShortSale', 'REO', 'Foreclosure', 'BankOwned')
- Also scan `PublicRemarks` for keywords: "foreclosure", "short sale", "bank owned", "REO", "as-is"
- Either exclude distressed sales or flag them with reduced weight in scoring
- In the report, clearly mark any distressed sale comps

### 12.6 Adjustment Quality Improvements

Our hardcoded adjustment values ($5K-$15K per bedroom) are guesses. Real agents derive these from paired sales analysis.

Better approach:
- Calculate local $/sqft from the comp set itself (not hardcoded)
- Derive bedroom/bathroom adjustments from comp data where possible
- Make ALL adjustment values configurable per market/zip code
- Let the broker override any adjustment value
- Flag when total adjustments exceed 25% of comp's sale price (Fannie Mae: heavy adjustments = unreliable comp)
- Weight reconciliation, not simple averaging — comps needing fewer adjustments get more weight

### 12.7 Days on Market Context

DOM tells a story that should influence comp weighting:
- DOM < 7: hot property, likely multiple offers, close price may be ABOVE true market
- DOM 7-30: healthy market, close price is reliable
- DOM 30-90: normal to slow, close price is reliable
- DOM > 90: stale listing, likely price reductions, close price may be BELOW market
- Weight comps with "normal" DOM (7-60 days) higher in scoring

### 12.8 Subject Property May Not Be in MLS

Broker might want a CMA for a property NOT currently listed (owner considering selling).

Fallback approach:
- Accept manual input: address, beds, baths, sqft, year built, lot size, features
- Use address geocoding for lat/long (for distance-based comp search)
- Run same comp search and analysis
- Note in report: "Subject property details provided by agent, not verified against MLS"

### 12.9 Comp Ranking Algorithm Improvements

Based on real-world CMA best practices:
- **Same subdivision weight: increase from 15% to 20-25%** — same subdivision = same school zone, HOA, neighborhood reputation. #1 thing agents look at.
- **Add PropertySubType matching** — townhouse comp for single-family subject is weak. Same subtype gets bonus.
- **Add age band matching** — 2020 build vs 1970 build are fundamentally different products.
- **Penalize comps with >25% total adjustments** — per Fannie Mae, these are unreliable.
- **Reconciliation over averaging** — final price estimate should weight comps needing fewest adjustments most heavily.

### 12.10 Report Must Include Confidence Indicators

Broker needs to know how reliable the CMA is:
- Number of comps found vs target (3-6)
- Average adjustment magnitude (lower = more reliable)
- Comp recency (all within 3 months = high confidence, 6-12 months = lower)
- Price clustering (tight cluster = high confidence, wide spread = low)
- Market conditions (months of supply, trending up/down/flat)
- Data quality flags (missing lat/long, missing concession data, distressed sales in set, etc.)
- Search tier used (Tier 1 = high confidence, Tier 3 = lower)

### 12.11 Updated API Call Budget Per CMA

| Step | Calls | Notes |
|------|-------|-------|
| Subject property lookup | 1 | By address or ListingKey, with $expand=Media for photo |
| Sold comps search (Tier 1) | 1 | $filter by zip/subdivision, status, sqft, beds, date |
| Sold comps search (Tier 2, if needed) | 0-1 | Wider criteria if Tier 1 < 3 comps |
| Sold comps search (Tier 3, if needed) | 0-1 | Widest criteria, last resort |
| Active competition | 1 | Same area, similar specs, StandardStatus eq 'Active' |
| Pending/under contract | 1 | Same area, StandardStatus in ('Pending','ActiveUnderContract') |
| **Total** | **4-6** | Well within rate limits |

All queries use `$select` to return only needed fields, `$top` to cap results, and `$expand=Media($select=MediaURL;$top=1;$orderby=Order)` to inline primary photo without separate media calls.

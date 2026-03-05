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

## 8. Open Questions (Updated 2026-03-05)

1. ~~What specific MLS?~~ **NTREIS** — confirmed on Trestle ✅
2. Will the Trestle account be under the broker's license or a tech provider account? **TBD**
3. What feed type was requested? (Need IDX Plus minimum) **TBD — verify on credential arrival**
4. ~~Target demo area?~~ **All of North Texas, especially north through Gainesville** ✅
5. Active listing analysis (absorption rate, competing inventory)? **TBD — decide after core CMA works**

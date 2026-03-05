# AI Listing Presentation Prep — Research & Plan

## Concept

Agent says in Discord: `!prep 123 Oak St, Denton TX 76201`
Bot generates a complete data-backed pricing brief for a listing appointment — comps, market stats, pricing recommendation, and talking points — in seconds instead of the 30-60 minutes it takes manually.

## Target User

- Real estate agents in North Texas (NTREIS/Trestle)
- Broker reviewing agent pricing strategy before appointments
- Coverage: all of North Texas through Gainesville

## What the Output Contains

### 1. Subject Property Profile
Pull from Trestle by address. Key fields:
- `LivingArea`, `BedroomsTotal`, `BathroomsTotalInteger`, `YearBuilt`
- `LotSizeArea`, `PropertySubType`, `Stories`, `GarageSpaces`, `PoolPrivateYN`
- If previously listed: `OriginalListPrice`, `PreviousListPrice`, `ClosePrice`, `CloseDate`
- `PublicRemarks` (property description)
- `PhotosCount` (for quality check)

### 2. Comparable Sold Properties (last 6 months)
Query: `StandardStatus eq 'Closed'` within 6 months, same zip or nearby, similar bed/bath/sqft.

For each comp display:
- Address, close price, close date
- Price per sqft (`ClosePrice / LivingArea`)
- Days on market (`DaysOnMarket` or calculated from `OnMarketTimestamp` to `CloseDate`)
- Bed/bath, sqft, year built
- List-to-close ratio (`ClosePrice / OriginalListPrice`)

Aggregate stats:
- Median close price, avg price/sqft, avg DOM
- Overall list-to-close ratio

### 3. Active Competition
Query: `StandardStatus eq 'Active'` with same filters.

Shows:
- Count of active listings in the competitive set
- Price range, avg price/sqft, avg DOM so far
- Highlights any direct competitors (very similar properties)

### 4. Market Health Metrics
Calculated from the query results:
- **Absorption rate**: active listings ÷ (closed per month over 6 months)
- **Months of supply** → buyer's/seller's market verdict
- **Price trend**: avg close price/sqft last 3 months vs prior 3 months
- **DOM trend**: same comparison
- **Pending count**: `StandardStatus eq 'Pending'` shows current demand

### 5. Suggested Price Range
- **Conservative**: below median comp price/sqft × subject sqft
- **Sweet spot**: median comp price/sqft × subject sqft
- **Aggressive**: above median, justified only with clear advantages
- Include list-to-close ratio so agent knows negotiation room

### 6. AI-Generated Talking Points
Bullet points the agent can use with the seller:
- "There are X active listings competing in your price range right now"
- "Similar homes are selling in Y days on average"
- "The market is currently [buyer's/seller's] with Z months of supply"
- "Homes priced at $X/sqft are closing at Y% of list price"

## Trestle API Research

### Authentication
- OAuth2 client credentials flow
- POST to `https://api-trestle.corelogic.com/trestle/oidc/connect/token`
- Returns bearer token

### Base URL
```
https://api-prod.corelogic.com/trestle/odata/Property
```

### Key Queries

**Subject property lookup:**
```
$filter=PostalCode eq '76201' and contains(UnparsedAddress,'123 Oak')
  and OriginatingSystemName eq 'NTREIS'
$select=ListingKey,UnparsedAddress,ListPrice,OriginalListPrice,ClosePrice,
  CloseDate,LivingArea,BedroomsTotal,BathroomsTotalInteger,YearBuilt,
  LotSizeArea,PropertySubType,Stories,GarageSpaces,PoolPrivateYN,
  PublicRemarks,PhotosCount,StandardStatus,DaysOnMarket,
  OnMarketTimestamp,PriceChangeTimestamp,PreviousListPrice
```

**Closed comps (6 months):**
```
$filter=StandardStatus eq 'Closed'
  and CloseDate ge 2025-09-05
  and PostalCode eq '76201'
  and PropertyType has PropertyEnums.PropertyType'Residential'
  and BedroomsTotal ge 2 and BedroomsTotal le 4
  and LivingArea ge 1200 and LivingArea le 1800
  and OriginatingSystemName eq 'NTREIS'
$select=ListingKey,UnparsedAddress,ClosePrice,CloseDate,OriginalListPrice,
  ListPrice,LivingArea,BedroomsTotal,BathroomsTotalInteger,YearBuilt,
  DaysOnMarket,LotSizeArea,GarageSpaces,PoolPrivateYN,PropertySubType
$orderby=CloseDate desc
$top=25
```

**Active competition:**
```
$filter=StandardStatus eq 'Active'
  and PostalCode eq '76201'
  and PropertyType has PropertyEnums.PropertyType'Residential'
  and BedroomsTotal ge 2 and BedroomsTotal le 4
  and LivingArea ge 1200 and LivingArea le 1800
  and OriginatingSystemName eq 'NTREIS'
$select=ListingKey,UnparsedAddress,ListPrice,LivingArea,BedroomsTotal,
  BathroomsTotalInteger,YearBuilt,DaysOnMarket,OnMarketTimestamp,
  PhotosCount,PropertySubType
$orderby=ListPrice asc
$top=25
```

**Pending (demand indicator):**
```
$filter=StandardStatus eq 'Pending'
  and PostalCode eq '76201'
  and PropertyType has PropertyEnums.PropertyType'Residential'
  and OriginatingSystemName eq 'NTREIS'
$count=true
$top=0
```

### InKeyIndex Fields (fast queries, up to 300k batch)
`ListingId`, `ListingKey`, `ModificationTimestamp`, `PhotosChangeTimestamp`, `PhotosCount`, `PostalCode`, `StandardStatus`

### Important Trestle Fields for CMA/Listing Prep

| Field | Type | Use |
|-------|------|-----|
| `ListPrice` | Decimal | Current asking price |
| `OriginalListPrice` | Decimal | First listed price (for list-to-close ratio) |
| `ClosePrice` | Decimal | What it actually sold for |
| `CloseDate` | Date | When it closed |
| `PreviousListPrice` | Decimal | Last price before current (price reduction tracking) |
| `PriceChangeTimestamp` | DateTimeOffset | When price last changed |
| `LivingArea` | Decimal | Total livable sqft |
| `BedroomsTotal` | Int32 | Bedrooms |
| `BathroomsTotalInteger` | Int32 | Total baths |
| `BathroomsFull` | Int32 | Full baths |
| `YearBuilt` | Int32 | Year built |
| `YearBuiltEffective` | Int32 | Year of major renovation |
| `LotSizeArea` | Decimal | Lot size |
| `Stories` | Int32 | Number of floors |
| `GarageSpaces` | Decimal | Garage spaces |
| `PoolPrivateYN` | Boolean | Has pool |
| `PropertyType` | Enum | Residential, Land, etc. |
| `PropertySubType` | Enum | SFR, Condo, Townhouse, etc. |
| `PropertyCondition` | Enum | Condition of property |
| `StandardStatus` | Enum | Active, Pending, Closed, Expired, Withdrawn |
| `DaysOnMarket` | Int32 | Days on market |
| `OnMarketTimestamp` | DateTimeOffset | When it went active |
| `StatusChangeTimestamp` | DateTimeOffset | Last status change |
| `PublicRemarks` | String | Property description |
| `PhotosCount` | Int32 | Number of photos |
| `Latitude` / `Longitude` | Decimal | Geo coordinates |
| `PostalCode` | String | Zip code (InKeyIndex — fast) |
| `City` | String | City name |
| `CountyOrParish` | String | County |
| `SchoolDistrict` | String | School district |
| `HighSchool` / `MiddleOrJuniorSchool` / `ElementarySchool` | String | School names |

## Discord Interaction Flow

```
1. Agent: !prep 123 Oak St, Denton TX 76201
2. Bot:   ⏳ Pulling comps and market data for 123 Oak St, Denton TX 76201...
3. Bot:   [Discord embed with full pricing brief]
          - Subject property summary
          - Top 5-6 comps table
          - Active competition summary
          - Market health (absorption, DOM trend, price trend)
          - Suggested price range (conservative / sweet spot / aggressive)
          - Talking points
4. Agent: (optional) !prep-pdf  → generates PDF, uploads to S3, returns presigned URL
```

## Technical Architecture

```
Discord command (!prep <address>)
  → Parse address (city, state, zip extraction)
  → Trestle API: search for subject property
  → Parallel:
      → Trestle API: closed comps (6 months, same zip, similar specs)
      → Trestle API: active listings (same filters)
      → Trestle API: pending count
  → Calculate metrics:
      → Price/sqft for each comp
      → Median/avg close price, price/sqft, DOM
      → List-to-close ratio
      → Absorption rate & months of supply
      → 3-month price & DOM trends
  → AI generates:
      → Suggested price range
      → Talking points tailored to the data
  → Format Discord embed
  → (Optional) PDF generation:
      → weasyprint or similar → HTML to PDF
      → Upload to S3
      → Generate presigned URL (7-day expiry)
      → Post link in Discord
```

## Comp Selection Logic

1. Start with same zip code, ±1 bed, ±20% sqft, same PropertyType
2. If < 5 comps, expand to adjacent zip codes
3. If still < 5, expand time window to 12 months
4. If > 15 comps, tighten: same bed count, ±10% sqft, same PropertySubType
5. Rank by similarity: closest sqft match, closest year built, same pool status, closest lot size
6. Present top 5-6 with the best similarity scores

## Adjustments (Phase 2+)

For more accurate pricing, apply standard adjustments:
- Pool: +$15-25k (North Texas typical)
- Garage: +$5-10k per space difference
- Sqft: use price/sqft from comps
- Age: newer = premium, calculate from YearBuilt or YearBuiltEffective
- Lot size: adjust for significant differences
- Condition: if PropertyCondition available

## Dependencies

- Trestle API credentials (waiting — see bd-2mb.7)
- NTREIS feed access (IDX Plus or higher for closed data)
- Discord bot infrastructure (existing via clawdbot)
- S3 bucket for PDF storage (if PDF feature enabled)

## Relationship to Other Ideas

- **CMA Generator (bd-2mb)**: This is essentially a streamlined, appointment-focused version of the CMA. Shares the same Trestle client, comp engine, and price analysis. The CMA epic's phases 1-3 directly feed this tool.
- **Lead Qualification Bot (bd-3ja)**: Uses similar property lookup and analysis, but triggered differently (lead evaluation vs. listing prep).
- **Market Pulse Digest (bd-1j9)**: The market health metrics (absorption, trends) overlap. Can share calculation logic.

## Open Questions

1. Radius-based search vs zip code? Trestle has Lat/Lng but no geo-radius filter — would need client-side distance calc
2. Should comp selection be adjustable via follow-up commands? (e.g., "expand to 12 months", "include 4 bed")
3. Phase 1 output: clean text summary vs full Discord embed with formatting?
4. How to handle properties not yet in MLS? (agent is prepping for a new listing that hasn't been entered)

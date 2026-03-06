# Market Pulse Digest — Research & Build Plan

**Bead:** bd-4xx (TBD)
**Status:** Research complete
**Last updated:** 2026-03-05

---

## 1. The Problem

Every morning, a North Texas broker opens NTREIS and manually scans for:
- What new listings hit the market overnight in his farm area?
- Did any listings get a price reduction?
- What went under contract (pending)?
- What sold yesterday and for how much?
- What expired or was withdrawn?
- Did anything come back on market?

This takes 15-30 minutes daily. It's repetitive, easy to miss things, and there's no analysis — just raw scanning. An AI agent can do this automatically, add context (price/sqft vs area avg, DOM analysis, list-to-sale ratio), and deliver it to Discord before the broker finishes his coffee.

---

## 2. What the Digest Contains

### 2.1 The "Hot Sheet" (Daily)

The industry term for this is a "hot sheet" — the daily summary of MLS changes. Here's what ours includes:

**🆕 New Listings**
- Properties that entered Active status in the last 24 hours
- Show: address, price, beds/baths/sqft, price/sqft, listing agent/office
- AI insight: "Priced 8% below area median — could move fast" or "Highest price/sqft in this zip this month"

**📉 Price Reductions**
- Properties where `ListPrice < PreviousListPrice` and `PriceChangeTimestamp` is within 24 hours
- Show: address, old price → new price, % reduction, DOM, original list price
- AI insight: "3rd reduction in 60 days — seller getting motivated" or "Now priced below recent comp at 4510 Elm ($385K)"

**📈 Price Increases** (rare but notable)
- Same logic, opposite direction
- Usually signals multiple offers or appraisal-driven repricing

**🤝 Under Contract (Pending/Active Under Contract)**
- Properties that changed to Pending or ActiveUnderContract
- Show: address, list price, DOM before going pending, beds/baths/sqft
- AI insight: "Went pending in 3 days — hot property" or "Was on market 90 days, likely negotiated down"

**✅ Sold (Closed)**
- Properties that changed to Closed status
- Show: address, list price vs close price, close date, DOM, beds/baths/sqft, price/sqft
- AI insight: "Sold 4% over asking — multiple offers likely" or "Sold 8% under list after 120 DOM"
- This is the most valuable section for pricing intelligence

**❌ Expired / Withdrawn / Canceled**
- Properties that went off-market without selling
- Show: address, original list price, final list price, total DOM
- AI insight: "Overpriced by ~12% vs comps — never reduced" or "Withdrawn after 5 DOM — likely personal reasons"

**🔄 Back on Market**
- Properties with `BackOnMarketTimestamp` in last 24 hours
- Show: address, price, previous status, why it's notable
- AI insight: "Was pending for 18 days — deal fell through. Financing issue likely."

### 2.2 Weekly Summary (Every Monday)

Aggregated stats for the broker's farm area:
- Total new listings this week vs last week
- Total closings this week vs last week
- Median price/sqft trend (4-week rolling)
- Average DOM for closings
- List-to-sale ratio (avg ClosePrice / ListPrice)
- Inventory count (active listings) — is it growing or shrinking?
- Absorption rate: at current pace, how many months of inventory?
- Price reduction rate: what % of active listings have had a reduction?

---

## 3. Trestle API Strategy

### 3.1 Key Fields for Change Detection

| What We're Tracking | Trestle Field | How to Detect |
|---------------------|---------------|---------------|
| New listings | `OriginalEntryTimestamp` | Timestamp within last 24h |
| Status changes | `StatusChangeTimestamp` + `StandardStatus` | Timestamp within 24h, check current status |
| Price changes | `PriceChangeTimestamp` + `ListPrice` vs `PreviousListPrice` | Timestamp within 24h |
| Back on market | `BackOnMarketTimestamp` | Timestamp within 24h |
| Any modification | `ModificationTimestamp` | Master change tracker |
| Previous status | `PreviousStandardStatus` | What status it was before |

### 3.2 Query Strategy

**Option A: ModificationTimestamp sweep (recommended)**

One query to catch ALL changes, then categorize locally:

```
GET /trestle/odata/Property
  ?$filter=ModificationTimestamp gt 2026-03-04T06:00:00Z
    and PropertyType eq 'Residential'
    and PostalCode in ('75024','75025','75034','75035','75070','75071','75072','75078','76240','76252','76259')
  &$select=ListingKey,ListingId,UnparsedAddress,City,PostalCode,
    StandardStatus,PreviousStandardStatus,MlsStatus,
    ListPrice,OriginalListPrice,PreviousListPrice,ClosePrice,CloseDate,
    BedroomsTotal,BathroomsTotalInteger,LivingArea,LotSizeSquareFeet,
    YearBuilt,GarageSpaces,PoolPrivateYN,PropertySubType,SubdivisionName,
    DaysOnMarket,CumulativeDaysOnMarket,
    ListAgentFullName,ListOfficeName,
    OriginalEntryTimestamp,OnMarketTimestamp,StatusChangeTimestamp,
    PriceChangeTimestamp,BackOnMarketTimestamp,OffMarketTimestamp,
    ModificationTimestamp,Latitude,Longitude
  &$orderby=ModificationTimestamp desc
  &$top=1000
```

Then in code, categorize each record:
- If `OriginalEntryTimestamp` within 24h → New Listing
- If `PriceChangeTimestamp` within 24h and `ListPrice != PreviousListPrice` → Price Change
- If `StatusChangeTimestamp` within 24h → Status Change (check `StandardStatus` for type)
- If `BackOnMarketTimestamp` within 24h → Back on Market

**Option B: Targeted queries (if quota is tight)**

Separate queries per category, using specific timestamps:

```
# New listings
$filter=OriginalEntryTimestamp gt 2026-03-04T06:00:00Z and PropertyType eq 'Residential' and PostalCode in (...)

# Price changes
$filter=PriceChangeTimestamp gt 2026-03-04T06:00:00Z and PropertyType eq 'Residential' and PostalCode in (...)

# Closed
$filter=StatusChangeTimestamp gt 2026-03-04T06:00:00Z and StandardStatus eq 'Closed' and PropertyType eq 'Residential' and PostalCode in (...)
```

**Recommendation:** Start with Option A. One query, ~2-5 API calls (paginated at 1000), well within the 7,200/hour quota. A daily digest needs maybe 5-10 queries total including enrichment.

### 3.3 Coverage Area — North Texas Zip Codes

The broker's farm area is "all of North Texas, especially north through Gainesville." Key zip codes to monitor:

**Frisco/Prosper/Celina corridor:**
75033, 75034, 75035, 75009, 75078

**Plano/Allen/McKinney:**
75024, 75025, 75013, 75002, 75069, 75070, 75071, 75072

**Denton/Aubrey/Pilot Point:**
76201, 76205, 76207, 76227, 76258, 76259

**Gainesville/Cooke County (north boundary):**
76240, 76252, 76233, 76264

**Sherman/Denison (northeast):**
75020, 75021, 75090, 75092

This is configurable — the broker can add/remove zip codes via Discord command.

### 3.4 Quota Budget

| Operation | Queries/day | Notes |
|-----------|-------------|-------|
| Daily digest (main sweep) | 3-5 | 1000 records/query, paginated |
| Sold enrichment (media/photos) | 5-10 | Optional: pull primary photo for sold comps |
| Weekly stats aggregation | 5-10 | Broader queries for trend data |
| Ad-hoc "what's new in 75024?" | 1-2 | On-demand from Discord |
| **Total daily** | **~15-25** | Well under 7,200/hour limit |

### 3.5 Feed Type Requirements

- New listings (Active): ✅ Available on IDX
- Price changes on active: ✅ Available on IDX
- Pending/Under Contract: ⚠️ May require IDX Plus
- Closed/Sold data: ❌ Requires IDX Plus or higher
- **Verdict:** Need IDX Plus minimum for the full digest. Without sold data, we lose the most valuable section.

---

## 4. Architecture

### 4.1 System Components

```
┌─────────────────────────────────────────┐
│           SCHEDULER (cron)               │
│  Daily: 6:00 AM CST                     │
│  Weekly: Monday 6:00 AM CST             │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│         TRESTLE DATA FETCHER             │
│  Query modified properties (last 24h)    │
│  Categorize: new, price change, status   │
│  Enrich with context (price/sqft, etc)   │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│         AI ANALYSIS ENGINE               │
│  Compare to area averages                │
│  Flag outliers and opportunities         │
│  Generate natural language insights      │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│         DISCORD FORMATTER                │
│  Format into readable digest             │
│  Use embeds for rich formatting          │
│  Post to #market-pulse channel           │
└─────────────────────────────────────────┘
```

### 4.2 Data Flow

1. Cron triggers at 6 AM CST
2. Fetch all modified residential properties in target zips from last 24h
3. Categorize each record into buckets (new, price change, pending, sold, expired, back on market)
4. For each bucket, calculate context metrics:
   - Price/sqft vs area median
   - DOM vs area average
   - List-to-sale ratio (for closed)
   - Price reduction % from original
5. AI generates 1-line insight per notable listing
6. Format into Discord message (or multiple messages if long)
7. Post to designated Discord channel

### 4.3 Local Data Store

Need a lightweight local store to:
- Track what we've already reported (avoid duplicates)
- Store historical data for trend calculations
- Cache area averages for comparison

SQLite is fine. Tables:
- `listings_seen` — ListingKey, last_status, last_price, first_seen_date
- `daily_snapshots` — date, zip, active_count, median_price, median_ppsf, avg_dom
- `digest_log` — date, message_id, records_reported

---

## 5. Discord Output Format

### 5.1 Daily Digest Example

```
☀️ NORTH TEXAS MARKET PULSE — Thu Mar 6, 2026

📊 OVERNIGHT SUMMARY
• 12 new listings | 5 price reductions | 3 went pending | 2 sold | 1 expired

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🆕 NEW LISTINGS (12)

🏠 4521 Elm Creek Dr, Prosper 75078
   $489,000 | 4/3 | 2,100 sqft | $233/sqft
   Built 2018 | 2-car garage | Pool
   💡 Priced 5% below area median ($245/sqft) — could move fast

🏠 812 Preston Rd, Frisco 75034
   $625,000 | 5/4 | 3,200 sqft | $195/sqft
   Built 2012 | 3-car garage
   💡 Largest new listing in 75034 this week

[...more listings...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📉 PRICE REDUCTIONS (5)

⬇️ 1900 Legacy Dr, Plano 75024
   $450,000 → $425,000 (-5.6%) | 45 DOM
   Original: $465,000 | Total reduction: 8.6%
   💡 2nd reduction — now at area median price/sqft

[...more reductions...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🤝 WENT PENDING (3)

⏳ 305 Stonebridge Ln, McKinney 75070
   $375,000 | 3/2 | 1,800 sqft | 6 DOM
   💡 Pending in under a week — priced right

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ SOLD (2)

💰 7744 Coit Rd, Plano 75024
   Listed: $410,000 | Sold: $405,000 (98.8% of list)
   3/2 | 1,950 sqft | $208/sqft | 22 DOM
   💡 Clean sale, close to asking

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ EXPIRED (1)

⛔ 9100 Ohio Dr, Plano 75024
   Listed: $550,000 | Final: $525,000 | 180 DOM
   💡 Overpriced vs comps (~$480K range). Never adjusted enough.
```

### 5.2 Weekly Summary Example

```
📈 WEEKLY MARKET REPORT — Week of Mar 1-7, 2026
North Texas Farm Area (32 zip codes)

                    This Week    Last Week    Change
New Listings           47           39        +20.5% ↑
Went Pending           28           31         -9.7% ↓
Sold/Closed            19           22        -13.6% ↓
Expired/Withdrawn       8            5        +60.0% ↑
Price Reductions       15           12        +25.0% ↑

📊 KEY METRICS
• Median List Price: $425,000 (↓ 1.2% from last week)
• Median Price/SqFt: $215 (flat)
• Avg DOM (closed): 34 days (↑ from 28)
• List-to-Sale Ratio: 97.2% (↓ from 98.1%)
• Active Inventory: 312 listings (↑ from 298)
• Months of Supply: 4.1 months (balanced market)
• Reduction Rate: 28% of active listings have been reduced

🔍 AI OBSERVATIONS
• Inventory growing — up 4.7% week over week. Buyer leverage increasing.
• Price reductions accelerating, especially in 75024 (Plano) and 75034 (Frisco).
• Closings slowing — DOM trending up. Sellers pricing aggressively are still moving fast.
• Gainesville area (76240) seeing unusual activity — 5 new listings, double the weekly avg.
```

### 5.3 On-Demand Commands

The broker can also ask for specific info in Discord:

```
"what's new in 75024?"        → New listings in that zip today
"price drops in Frisco"       → Recent reductions in Frisco
"what sold in McKinney?"      → Recent closings in McKinney
"market stats for Prosper"    → Quick stats for Prosper zips
"add zip 76234"               → Add a zip code to monitoring
"remove zip 75090"            → Remove a zip code
```

---

## 6. Build Phases

### Phase 1: Trestle Client + Basic Fetch
- OAuth2 auth (reuse from CMA plan)
- Query builder for Property resource with timestamp filters
- Fetch modified properties for target zip codes
- Categorize into buckets (new, price change, status change)
- Store in SQLite

### Phase 2: Daily Digest Formatter
- Format categorized data into Discord-friendly messages
- Calculate context metrics (price/sqft, DOM, vs area avg)
- Handle message length limits (Discord max 2000 chars per message — split into multiple)
- Post to Discord channel

### Phase 3: AI Insights
- For each notable listing, generate a 1-line insight
- Compare to recent comps and area averages
- Flag outliers, opportunities, and trends

### Phase 4: Weekly Summary
- Aggregate daily data into weekly stats
- Calculate week-over-week trends
- Months of supply / absorption rate
- AI-generated market narrative

### Phase 5: On-Demand Queries
- Discord commands for ad-hoc lookups
- Zip code management (add/remove from watch list)
- "What sold in [city]?" type queries

---

## 7. Tech Stack

| Component | Choice | Why |
|-----------|--------|-----|
| Language | Python | Matches CMA/Lead bot stack |
| Trestle client | `requests` + OAuth2 | Shared with CMA tool |
| Data store | SQLite | Lightweight, no server needed |
| Scheduler | cron (Linux) or APScheduler (Python) | Simple, reliable |
| Discord | OpenClaw bot | Already in use |
| AI insights | LLM (agent) | Natural language analysis |

---

## 8. Shared Infrastructure with Other Tools

This digest shares significant code with the CMA Generator and Lead Bot:

| Component | Shared? | Notes |
|-----------|---------|-------|
| Trestle OAuth2 client | ✅ Yes | Same auth, same token cache |
| OData query builder | ✅ Yes | Same filter/select/orderby patterns |
| Property data model | ✅ Yes | Same fields, same parsing |
| Area averages/stats | ✅ Yes | Digest calculates them, CMA uses them |
| Discord bot framework | ✅ Yes | Same bot, different commands |
| SQLite data store | ✅ Yes | Shared DB, different tables |

Building the digest first actually creates the foundation for the CMA and Lead tools.

---

## 9. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Feed type is IDX only (no sold data) | High — lose best section | Verify on credential arrival; request upgrade |
| Too many listings in target area | Medium — long messages | Paginate, summarize, show top 10 per category with "and 15 more" |
| Discord 2000 char message limit | Medium — formatting | Split into multiple messages, one per category |
| Trestle data delay | Low — data not real-time | Trestle updates every few minutes; 6 AM digest captures overnight changes |
| Missing fields (nulls) | Low | Graceful fallbacks; skip insight if data insufficient |
| Zip code list too broad | Low | Start narrow, let broker expand |

---

## 10. Open Questions

1. What time does the broker want the daily digest? (Assuming 6 AM CST)
2. Does he want weekend digests or weekday only?
3. Which zip codes to start with? (Need his specific farm area list)
4. Does he want agent/office names shown? (Some brokers care about competitor activity)
5. Should the digest include rental listings or residential sales only?
6. Feed type confirmation — need IDX Plus minimum for sold data

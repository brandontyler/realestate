---
name: mls
description: MLS real estate data access via RESO Web API. Use when users ask about properties, listings, comps, CMAs, market stats, property lookups, sold data, active listings, or any real estate data query. Trigger phrases include "find properties", "look up", "comps for", "CMA", "what sold", "active listings", "market stats", "price per sqft", "days on market", any address lookup, or any MLS/real estate data request.
---

# MLS Data Access Skill

Query real estate MLS data via the RESO Web API. The client lives at `/home/tylerbtt/code/personal/realestate/mls/` and supports Bridge Interactive (dev) and Trestle/NTREIS (production).

## Quick Start

All scripts must start with:
```python
import sys; sys.path.insert(0, "/home/tylerbtt/code/personal/realestate")
from dotenv import load_dotenv; load_dotenv("/home/tylerbtt/code/personal/realestate/.env")
from mls.client import create_client
client = create_client()
```

## Core Operations

### Search by address
```python
result = client.query("Property",
    filter="UnparsedAddress eq '123 Main St, Austin TX 78701'",
    select=["ListingKey","UnparsedAddress","ListPrice","StandardStatus",
            "BedroomsTotal","BathroomsTotalInteger","LivingArea","YearBuilt",
            "LotSizeSquareFeet","GarageSpaces","Latitude","Longitude",
            "SubdivisionName","PropertySubType","Media"],
    top=5)
```

For partial/fuzzy address matching, use `contains`:
```python
filter="contains(UnparsedAddress, '123 Main')"
```

### Find sold comps near a property
```python
# By zip code
result = client.query("Property",
    filter="StandardStatus eq 'Closed' and PostalCode eq '78734' "
           "and BedroomsTotal ge 3 and BedroomsTotal le 5 "
           "and LivingArea ge 1600 and LivingArea le 2400 "
           "and CloseDate ge 2025-09-01",
    select=["ListingKey","UnparsedAddress","ListPrice","CloseDate",
            "BedroomsTotal","BathroomsTotalInteger","LivingArea","YearBuilt",
            "LotSizeSquareFeet","GarageSpaces","PoolPrivateYN",
            "Latitude","Longitude","SubdivisionName","PropertySubType"],
    orderby="CloseDate desc",
    top=50, count=True)
```

### Active competition
```python
result = client.query("Property",
    filter="StandardStatus eq 'Active' and PostalCode eq '78734' "
           "and BedroomsTotal ge 3 and BedroomsTotal le 5",
    select=["ListingKey","UnparsedAddress","ListPrice","LivingArea",
            "BedroomsTotal","BathroomsTotalInteger","OnMarketDate"],
    top=50, count=True)
```

### Pending/under contract
```python
result = client.query("Property",
    filter="(StandardStatus eq 'Pending' or StandardStatus eq 'ActiveUnderContract') "
           "and PostalCode eq '78734'",
    top=50, count=True)
```

### Single property by key
```python
prop = client.get_by_key("Property", "abc123def",
    select=["ListingKey","UnparsedAddress","ListPrice","Media"])
```

### Pagination
```python
result = client.query("Property", filter="...", top=200)
while "@odata.nextLink" in result:
    result = client.fetch_next(result["@odata.nextLink"])
    # process result["value"]
```

### Geo search (Bridge only)
```python
# Properties within 2 miles of a point
result = client.query("Property",
    filter="geo.distance(Coordinates, POINT(-97.7431 30.2672)) le 2 "
           "and StandardStatus eq 'Closed'",
    top=50)
```

### Rate limit status
```python
print(client.rate_limiter.status())
```

## Available Resources

| Resource | Description |
|----------|-------------|
| Property | Listings — active, closed, pending, withdrawn |
| Member | Real estate agents |
| Office | Brokerages |
| OpenHouse | Open house events |
| Media | Photos (on Bridge actris_ref, use `$select=Media` on Property instead) |

## Key Property Fields

**Identity:** ListingKey (unique), ListingId, UnparsedAddress, City, PostalCode, StateOrProvince, SubdivisionName, CountyOrParish

**Location:** Use `geo.distance(Coordinates, POINT(lng lat))` for radius search on Bridge. No Latitude/Longitude fields on actris_ref.

**Status:** StandardStatus (Active/ActiveUnderContract/Closed/Pending/Withdrawn/Expired), MlsStatus, CloseDate, OffMarketDate, ListingContractDate

**Pricing:** ListPrice, ClosePrice*, OriginalListPrice*, PreviousListPrice*

**Structure:** BedroomsTotal, BathroomsTotalInteger, BathroomsFull, BathroomsHalf, LivingArea, LotSizeSquareFeet, LotSizeAcres, YearBuilt, StoriesTotal, BuildingAreaTotal

**Features:** GarageSpaces, GarageYN, PoolPrivateYN, PropertyType, PropertySubType, ConstructionMaterials, Roof, Heating, Cooling, View, Flooring, InteriorFeatures

**Market:** DaysOnMarket*, CumulativeDaysOnMarket*, ListingContractDate, PriceChangeTimestamp

**Tax:** TaxAssessedValue, TaxLegalDescription (TaxAnnualAmount* missing on actris_ref)

**Media:** Media (array of {MediaURL, Order, MediaCategory, ShortDescription}) — use `$select=Media`, NOT `$expand=Media`

**Agent/Office:** ListAgentFullName, ListOfficeName, BuyerAgentFullName, BuyerOfficeName

*Fields marked with * do NOT exist on Bridge actris_ref. They exist on Trestle/NTREIS.

## OData Filter Syntax

```
eq, ne, gt, ge, lt, le          — comparison
and, or, not                     — logical
contains(Field, 'value')         — substring match
startswith(Field, 'value')       — prefix match
Field eq null / Field ne null    — null checks
```

Date literals are unquoted: `CloseDate ge 2025-01-01`
String literals use single quotes: `City eq 'Austin'`
Collections: `StandardStatus eq 'Active' or StandardStatus eq 'Closed'`

## Current Provider: Bridge (ACTRIS Reference Server)

- Dataset: actris_ref (52k+ Austin TX listings, real data)
- Rate limits: 5,000/hr, 334/min burst
- Quirks: No ClosePrice/DaysOnMarket fields; use `$select=Media` not `$expand=Media`; no `$orderby` inside `$expand`

## Approach: Let the Model Think

The MLS client is a data access tool. Do NOT build rigid comp selection algorithms, scoring formulas, or adjustment calculators in code. Instead:

1. **Query the data** using the client
2. **Reason about the results** — which comps are most relevant and why
3. **Explain your reasoning** — the broker wants to understand the logic
4. **Iterate** — if the first search is too narrow/wide, adjust and re-query

The model's judgment about what makes a good comp is more valuable than any hardcoded formula.

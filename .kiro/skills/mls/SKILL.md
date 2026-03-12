---
name: mls
description: MLS real estate data access via RESO Web API. Use when users ask about properties, listings, comps, CMAs, market stats, property lookups, sold data, active listings, or any real estate data query. Trigger phrases include "find properties", "look up", "comps for", "CMA", "what sold", "active listings", "market stats", "price per sqft", "days on market", any address lookup, or any MLS/real estate data request.
---

# MLS Data Access Skill

Client lives at `/home/tylerbtt/code/personal/realestate/mls/`. Supports Bridge Interactive (dev) and Trestle/NTREIS (production).

## Quick Start

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
    filter="contains(UnparsedAddress, '123 Main')",
    select=["ListingKey","UnparsedAddress","ListPrice","StandardStatus",
            "BedroomsTotal","BathroomsTotalInteger","LivingArea","YearBuilt",
            "LotSizeSquareFeet","GarageSpaces","SubdivisionName","PropertySubType","Media"],
    top=5)
```

### Sold comps
```python
result = client.query("Property",
    filter="StandardStatus eq 'Closed' and PostalCode eq '78734' "
           "and BedroomsTotal ge 3 and BedroomsTotal le 5 "
           "and LivingArea ge 1600 and LivingArea le 2400 "
           "and CloseDate ge 2025-09-01",
    select=["ListingKey","UnparsedAddress","ListPrice","CloseDate",
            "BedroomsTotal","BathroomsTotalInteger","LivingArea","YearBuilt",
            "LotSizeSquareFeet","GarageSpaces","PoolPrivateYN",
            "SubdivisionName","PropertySubType"],
    orderby="CloseDate desc", top=50, count=True)
```

### Active / Pending
```python
# Active
client.query("Property", filter="StandardStatus eq 'Active' and PostalCode eq '78734'", top=50, count=True)
# Pending
client.query("Property", filter="(StandardStatus eq 'Pending' or StandardStatus eq 'ActiveUnderContract') and PostalCode eq '78734'", top=50, count=True)
```

### Single property / Pagination / Geo search
```python
prop = client.get_by_key("Property", "abc123def", select=[...])

# Pagination
while "@odata.nextLink" in result:
    result = client.fetch_next(result["@odata.nextLink"])

# Geo (Bridge only)
client.query("Property", filter="geo.distance(Coordinates, POINT(-97.7431 30.2672)) le 2 and StandardStatus eq 'Closed'", top=50)
```

## Resources

Property, Member, Office, OpenHouse, Media

## Key Fields

**Identity:** ListingKey, ListingId, UnparsedAddress, City, PostalCode, SubdivisionName, CountyOrParish

**Status:** StandardStatus (Active/ActiveUnderContract/Closed/Pending/Withdrawn/Expired), CloseDate, ListingContractDate

**Pricing:** ListPrice, ClosePrice*, OriginalListPrice*

**Structure:** BedroomsTotal, BathroomsTotalInteger, BathroomsFull, BathroomsHalf, LivingArea, LotSizeSquareFeet, LotSizeAcres, YearBuilt, StoriesTotal, GarageSpaces, PoolPrivateYN, PropertyType, PropertySubType

**Tax:** TaxAssessedValue, TaxLegalDescription

**Media:** Use `$select=Media` (NOT `$expand=Media`). Array of {MediaURL, Order, MediaCategory, ShortDescription}.

**Agent:** ListAgentFullName, ListOfficeName, BuyerAgentFullName, BuyerOfficeName

*Fields marked * do NOT exist on Bridge actris_ref.

## Bridge actris_ref Quirks

- Dataset: `actris_ref` (52k+ Austin TX listings). Rate limits: 5,000/hr, 334/min burst.
- Missing: ClosePrice, DaysOnMarket, CumulativeDaysOnMarket, OriginalListPrice, PreviousListPrice, Latitude, Longitude, OnMarketDate, Stories, RoomsTotal, TaxAnnualAmount
- Use `StoriesTotal` not `Stories`; `geo.distance(Coordinates, POINT(lng lat))` for location
- `$select=Media` not `$expand=Media`; no `$orderby` inside `$expand`

## OData Filter Syntax

`eq, ne, gt, ge, lt, le` | `and, or, not` | `contains(Field, 'value')` | `startswith(Field, 'value')`

Dates unquoted: `CloseDate ge 2025-01-01`. Strings single-quoted: `City eq 'Austin'`.

## Approach

Query the data, reason about results, explain reasoning, iterate if search is too narrow/wide. The model's judgment about comp quality is more valuable than any formula.

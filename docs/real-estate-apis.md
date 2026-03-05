# Real Estate APIs Reference

> Last updated: March 4, 2026

## Property Data & Listings

### Zillow API
- **URL:** https://www.zillowgroup.com/developers/
- **Data:** Property details, Zestimates, comps, sales history
- **Coverage:** 150M+ US properties
- **Access:** Free tier with rate limits; commercial usage restrictions

### Realtor.com API
- **URL:** https://www.realtor.com/
- **Data:** Active MLS listings, agent/broker info, market analytics, price trends
- **Coverage:** National MLS coverage
- **Access:** Free tier with limited requests/month; authentication required

### Redfin API
- **URL:** https://www.redfin.com/
- **Data:** Real-time listing updates, valuations, walk scores, school ratings
- **Coverage:** Major metro areas (expanding)
- **Access:** Geographic restrictions; usage quotas

### ATTOM Data API
- **URL:** https://www.attomdata.com/solutions/property-data-api/
- **Data:** Tax records, sales history, zoning, environmental hazards, crime rates, school ratings
- **Coverage:** 155M+ US properties
- **Access:** Trial available; usage-based pricing

### Estated API
- **URL:** https://estated.com/
- **Data:** Ownership info, mortgage records, tax assessments, lien info
- **Coverage:** 150M+ US properties
- **Access:** Limited free requests; pay-per-use

### RealEstateAPI (REAPI)
- **URL:** https://www.realestateapi.com/
- **Data:** Property data, MLS integration, GeoJSON parcel boundaries, owner contacts
- **Coverage:** National with MLS integration
- **Access:** Developer trial available; custom pricing

### DataTree API (First American)
- **URL:** https://web.datatree.com/
- **Data:** Property records, recorded documents, HOA/PACE lien data
- **Coverage:** Complete US coverage
- **Access:** Trial available; enterprise licensing

---

## Valuations & Investment Analysis

### HouseCanary API
- **URL:** https://www.housecanary.com/
- **Data:** ML-powered valuations, 36-month forecasts, risk assessment, transaction history
- **Coverage:** National
- **Access:** Trial; subscription-based

### Mashvisor API
- **URL:** https://www.mashvisor.com/data-api
- **Data:** Rental income predictions (Airbnb + traditional), occupancy rates, cash flow analysis
- **Coverage:** US markets (rental investment focus)
- **Access:** Trial; subscription-based

### RentCast API
- **URL:** https://developers.rentcast.io
- **Data:** Rent estimates, comps, active listings, market trends, owner details
- **Coverage:** Nationwide
- **Access:** Competitive pricing; good documentation

### CoreLogic API
- **URL:** https://www.corelogic.com.au/software-solutions/corelogic-apis
- **Data:** 200+ data sources, AI analytics, building permits, risk assessment
- **Coverage:** 155M+ properties (monthly updates)
- **Access:** Enterprise pricing

---

## Neighborhood & Location Data

### Google Maps API
- **URL:** https://developers.google.com/maps
- **Data:** Mapping, Street View, commute times, nearby amenities, geocoding
- **Coverage:** Global
- **Access:** Free monthly quota; billing required for high volume

### Zillow Neighborhood Data
- **URL:** Part of Zillow API (see above)
- **Data:** Demographics, affordability stats, boundary shapefiles, school data
- **Coverage:** US neighborhoods, cities, ZIP codes

---

## MLS Access (Requires Broker Credentials)

### SimplyRETS
- **URL:** http://www.simplyrets.com
- **Data:** Direct MLS feed via RESTful API — ideal for IDX sites
- **Access:** Requires MLS membership

### Bridge Interactive
- **URL:** https://bridgedataoutput.com/
- **Data:** MLS data via RESO standards
- **Access:** Requires MLS membership or approved vendor status

### Repliers
- **URL:** https://repliers.io
- **Data:** MLS data across US & Canada, AI-powered natural language search
- **Access:** Requires MLS connection

---

## Mortgage & Financing

### Zillow Mortgage APIs
- **Data:** Current mortgage rates by state/loan type, monthly payment calculators, affordability calculators
- **Access:** Part of Zillow API

---

## Recommended Combinations for a Brokerage

| Use Case | Recommended APIs |
|----------|-----------------|
| Active listings + IDX site | MLS feed (SimplyRETS or Bridge) |
| Property records & tax data | ATTOM or Estated |
| Rental/investment analysis | RentCast or Mashvisor |
| Valuations & forecasting | HouseCanary |
| Location context & mapping | Google Maps |
| Comps & market trends | Zillow + ATTOM |

---

## Notes

- As a broker, MLS access is the most valuable data source — APIs like SimplyRETS and Bridge plug directly into that feed.
- Public APIs (Zillow, ATTOM, etc.) supplement MLS data with tax records, valuations, and neighborhood info the MLS doesn't provide.
- Most "free tiers" have rate limits and commercial restrictions — read the terms before building anything production-facing.
- RESO (Real Estate Standards Organization) is the industry standard for MLS data formats — look for RESO-compliant APIs for easier integration.

# NTREIS MLS Access Guide

> Last updated: March 4, 2026

## Overview

**NTREIS** (North Texas Real Estate Information Systems) is the primary MLS for North Texas, serving 48,000+ real estate professionals across Dallas, Fort Worth, Arlington, Denton, and surrounding areas.

- Website: https://www.ntreis.net
- RESO listing: https://www.reso.org/web-api-examples/mls/north-texas-re-info-systems/

## API Access Options

### 1. RESO Web API (Recommended)
- NTREIS supports the RESO Web API standard
- Data returned in OData format (standardized, easy to parse)
- Modern REST-based protocol replacing legacy RETS
- **To get access:** Contact NTREIS directly as a broker/member and request RESO Web API credentials

### 2. Trestle (CoreLogic)
- Many NTREIS members access data through CoreLogic's Trestle platform
- RESO-compliant
- If the brokerage's MLS login goes through a CoreLogic portal, Trestle is likely the backend

### 3. Third-Party Middleware (Approved Vendors)
| Vendor | URL | Notes |
|--------|-----|-------|
| SimplyRETS | https://simplyrets.com | Clean REST API, supports NTREIS |
| IDX Broker | https://idxbroker.com | Approved NTREIS IDX vendor |
| Showcase IDX | https://showcaseidx.com | Approved NTREIS IDX vendor |

## Feed Types

| Type | Description | Use Case |
|------|-------------|----------|
| IDX | Display other agents' listings on your site | Public-facing listing search |
| VOW | More data than IDX, requires user registration | Client portals with extra detail |
| RETS/RESO Feed | Raw data access | Custom apps, analytics, CRM integration |

## Steps to Get Access

1. Log into the NTREIS member portal
2. Look for "Data Feeds," "API Access," or "Vendor/Developer" section
3. If not found, call NTREIS help desk and request RESO Web API credentials
4. As a brokerage owner, emphasize you're building internal tools — stronger case for raw feed access
5. Once credentials are issued, we can start building integrations

## Other Texas MLS Systems (Secondary)

- **Unlock MLS** (formerly HAR) — Houston area, expanding statewide: https://www.unlockmls.com
- **TX State MLS** — statewide coverage, $45/mo, no board membership required: https://texasstatemls.com
- **MyStateMLS** — nationwide network, Texas coverage included: https://www.mystatemls.com

## What We Can Build Once We Have Credentials

- Listing search and filtering tools
- Automated CMA (comparative market analysis) reports
- New listing alerts and monitoring
- Comp pulling for valuations
- Market trend dashboards
- Feed data into a custom CRM or deal tracker

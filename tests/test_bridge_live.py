"""Smoke test — verify Bridge API client works against live ACTRIS data."""

import json
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from mls.client import create_client

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


def main():
    client = create_client("bridge")

    # 1. Basic query — 1 property, minimal fields
    print("=== Test 1: Basic query ===")
    result = client.query(
        "Property",
        select=["ListingKey", "UnparsedAddress", "ListPrice", "StandardStatus"],
        top=1,
        count=True,
    )
    print(f"Total properties: {result.get('@odata.count')}")
    print(f"First listing: {json.dumps(result['value'][0], indent=2)}")

    # 2. Filtered query — closed sales in Austin
    print("\n=== Test 2: Closed sales ===")
    result = client.query(
        "Property",
        filter="StandardStatus eq 'Closed' and City eq 'Austin'",
        select=["ListingKey", "UnparsedAddress", "ListPrice", "CloseDate"],
        orderby="CloseDate desc",
        top=3,
        count=True,
    )
    print(f"Closed sales in Austin: {result.get('@odata.count')}")
    for p in result["value"]:
        print(f"  {p.get('UnparsedAddress')} — ${p.get('ListPrice'):,} (closed {p.get('CloseDate')})")

    # 3. Query with media (actris_ref: Media is a field, not an $expand)
    print("\n=== Test 3: With media ===")
    result = client.query(
        "Property",
        filter="StandardStatus eq 'Active'",
        select=["ListingKey", "UnparsedAddress", "ListPrice", "Media"],
        top=1,
    )
    prop = result["value"][0]
    media = prop.get("Media", [])
    print(f"  {prop.get('UnparsedAddress')} — ${prop.get('ListPrice'):,}")
    print(f"  Photo: {media[0]['MediaURL'] if media else 'none'}")

    # 4. Pagination — fetch next page
    print("\n=== Test 4: Pagination ===")
    result = client.query(
        "Property",
        select=["ListingKey"],
        top=2,
    )
    next_link = result.get("@odata.nextLink")
    print(f"Page 1: {len(result['value'])} results")
    if next_link:
        page2 = client.fetch_next(next_link)
        print(f"Page 2: {len(page2['value'])} results")
        assert result["value"][0]["ListingKey"] != page2["value"][0]["ListingKey"], "Pages should differ"
        print("  Pages contain different listings ✓")

    # 5. Single entity by key
    print("\n=== Test 5: Get by key ===")
    key = result["value"][0]["ListingKey"]
    single = client.get_by_key("Property", key)
    print(f"  Fetched: {single.get('UnparsedAddress', 'N/A')}")

    # 6. Rate limit status
    rl = client.rate_limiter
    print(f"\n=== Rate limits ===")
    print(f"Hourly:  {rl.hourly.remaining}/{rl.hourly.limit}")
    print(f"Burst:   {rl.burst.remaining}/{rl.burst.limit}")

    print("\n✓ All tests passed")


if __name__ == "__main__":
    main()

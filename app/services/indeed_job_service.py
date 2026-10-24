import json
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from app.services.indeed_mcp_client import (
    indeed_mcp_client,
    IndeedMCPError,
)

logger = logging.getLogger(__name__)

COUNTRY_DOMAINS = {
    "argentina": "ar.indeed.com",
    "australia": "au.indeed.com",
    "austria": "at.indeed.com",
    "belgium": "be.indeed.com",
    "brazil": "br.indeed.com",
    "canada": "ca.indeed.com",
    "denmark": "dk.indeed.com",
    "france": "fr.indeed.com",
    "germany": "de.indeed.com",
    "india": "in.indeed.com",
    "ireland": "ie.indeed.com",
    "italy": "it.indeed.com",
    "japan": "jp.indeed.com",
    "mexico": "mx.indeed.com",
    "netherlands": "nl.indeed.com",
    "new zealand": "nz.indeed.com",
    "norway": "no.indeed.com",
    "poland": "pl.indeed.com",
    "portugal": "pt.indeed.com",
    "singapore": "sg.indeed.com",
    "south africa": "za.indeed.com",
    "spain": "es.indeed.com",
    "sweden": "se.indeed.com",
    "switzerland": "ch.indeed.com",
    "united kingdom": "uk.indeed.com",
    "united states": "www.indeed.com",
}

COUNTRY_ALIASES = {
    "uk": "united kingdom",
    "usa": "united states",
    "us": "united states",
}


class IndeedJobSearchError(Exception):
    """Raised when Indeed search results cannot be processed."""


def infer_domain(
    country: str | None,
    location: str | None,
) -> str | None:
    """Resolve the Indeed domain from the explicit country first."""
    country_text = (country or "").strip().lower()
    location_text = (location or "").strip().lower()

    country_text = COUNTRY_ALIASES.get(country_text, country_text)

    if country_text in COUNTRY_DOMAINS:
        return COUNTRY_DOMAINS[country_text]

    # Avoid short aliases such as "us" matching arbitrary words.
    combined = f"{country_text} {location_text}"

    for name in sorted(COUNTRY_DOMAINS, key=len, reverse=True):
        if name in combined:
            return COUNTRY_DOMAINS[name]

    return None


def parse_provider_response(raw: Any) -> Any:
    """Unwrap MCP content and nested JSON strings."""
    if isinstance(raw, str):
        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError:
            return {"raw_text": raw}

        return parse_provider_response(decoded)

    if isinstance(raw, list):
        # MCP content sometimes arrives as a list of text blocks.
        if len(raw) == 1 and isinstance(raw[0], dict):
            block = raw[0]

            if isinstance(block.get("text"), str):
                return parse_provider_response(block["text"])

        return raw

    if isinstance(raw, dict):
        # LangChain/MCP message-style result.
        content = raw.get("content")
        if isinstance(content, list):
            return parse_provider_response(content)

        # HasData's outer response may contain the real result in "json".
        if "json" in raw:
            return parse_provider_response(raw["json"])

        # Some responses wrap the actual JSON in a text string.
        if "text" in raw and not any(
            key in raw for key in ("jobs", "searchInformation")
        ):
            return parse_provider_response(raw["text"])

        return raw

    # Handle LangChain message objects.
    content = getattr(raw, "content", None)
    if content is not None:
        return parse_provider_response(content)

    return {"raw_text": str(raw)}


def extract_jobs(payload: Any) -> list[dict[str, Any]]:
    """Extract actual listings from the normalized provider payload."""
    if isinstance(payload, list):
        # Some MCP responses are arrays of text-wrapped result objects.
        if len(payload) == 1 and isinstance(payload[0], dict):
            if isinstance(payload[0].get("text"), str):
                nested = parse_provider_response(payload[0]["text"])
                return extract_jobs(nested)

        if all(isinstance(item, dict) for item in payload):
            return payload

        raise IndeedJobSearchError("Unrecognized job-list response.")

    if not isinstance(payload, dict):
        raise IndeedJobSearchError("Unrecognized provider response.")

    jobs = payload.get("jobs")

    if isinstance(jobs, list) and all(
        isinstance(job, dict) for job in jobs
    ):
        return jobs

    # Recognize an explicit empty result.
    if isinstance(jobs, list) and not jobs:
        return []

    raise IndeedJobSearchError(
        "The provider response did not contain a recognized jobs array."
    )


def extract_total_results(payload: Any) -> int | None:
    """Read the provider's estimated total from searchInformation."""
    if not isinstance(payload, dict):
        return None

    info = payload.get("searchInformation", {})
    if not isinstance(info, dict):
        return None

    value = info.get("totalResults")

    try:
        return int(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


def is_sponsored(job: dict[str, Any]) -> bool:
    value = job.get("sponsored", False)

    if isinstance(value, bool):
        return value

    return str(value).strip().lower() in {"true", "1", "yes"}


def location_matches(
    job: dict[str, Any],
    requested_location: str,
    country: str | None,
) -> bool:
    """
    Safety filter for location.

    Bengaluru/Bangalore searches accept Bengaluru/Bangalore postings,
    Karnataka postings, and clearly India-based remote postings.
    """
    actual = str(job.get("location") or "").strip().lower()
    requested = requested_location.strip().lower()
    country_text = (country or "").strip().lower()

    if not actual:
        return False

    # Explicit city aliases.
    city_aliases = {
        "bengaluru": ("bengaluru", "bangalore"),
        "bangalore": ("bengaluru", "bangalore"),
    }

    aliases = city_aliases.get(requested, (requested,))

    if any(alias in actual for alias in aliases):
        return True

    # Allow regional results only when the requested city is in Karnataka.
    if (
        any(alias in requested for alias in ("bengaluru", "bangalore"))
        and "karnataka" in actual
        and ("india" in actual or country_text == "india")
    ):
        return True

    # Include remote jobs only when they explicitly indicate India.
    if "remote" in actual and (
        "india" in actual or "india" in country_text
    ):
        return True

    return False


def is_within_last_30_days(job: dict[str, Any]) -> bool:
    """Apply a local date safety filter when a posting date is available."""
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=30)

    iso_date = job.get("isoDate") or job.get("iso_date")

    if iso_date:
        try:
            posted = datetime.fromisoformat(
                str(iso_date).replace("Z", "+00:00")
            )

            if posted.tzinfo is None:
                posted = posted.replace(tzinfo=timezone.utc)

            return cutoff <= posted.astimezone(timezone.utc) <= now
        except ValueError:
            pass

    # Fallback for relative dates, e.g. "5 days ago".
    date_text = str(job.get("date") or "").strip().lower()

    if any(
        phrase in date_text
        for phrase in ("just posted", "today", "yesterday")
    ):
        return True

    match = re.search(r"(\d+)\s+days?\s+ago", date_text)
    if match:
        return int(match.group(1)) <= 30

    # Do not claim an unknown posting date is recent.
    return False


class IndeedJobService:
    async def search_jobs(
        self,
        *,
        keyword: str,
        location: str,
        country: str | None = None,
    ) -> dict[str, Any]:
        keyword = keyword.strip()
        location = location.strip()

        if not keyword:
            raise ValueError("Job keyword cannot be empty.")

        if not location:
            raise ValueError("Job location cannot be empty.")

        domain = infer_domain(country, location)

        # Include the country in the query location to reduce ambiguity.
        provider_location = location
        if country and country.lower() not in location.lower():
            provider_location = f"{location}, {country}"

        try:
            raw = await indeed_mcp_client.search_jobs(
                keyword=keyword,
                location=provider_location,
                domain=domain,
                date_posted=30,
            )
        except IndeedMCPError:
            raise
        except Exception as exc:
            logger.exception("Unexpected Indeed search failure.")
            raise IndeedJobSearchError(
                "Unable to complete the Indeed job search."
            ) from exc

        payload = parse_provider_response(raw)
        provider_jobs = extract_jobs(payload)
        provider_total = extract_total_results(payload)

        # Exclude sponsored results and locations outside the requested area.
        location_filtered = [
            job
            for job in provider_jobs
            if location_matches(job, location, country)
        ]

        organic_jobs = [
            job for job in location_filtered if not is_sponsored(job)
        ]

        recent_jobs = [
            job for job in organic_jobs if is_within_last_30_days(job)
        ]

        logger.info(
            "Indeed results: provider_page=%d, location_matched=%d, "
            "organic=%d, recent=%d",
            len(provider_jobs),
            len(location_filtered),
            len(organic_jobs),
            len(recent_jobs),
        )

        return {
            "status": "success",
            "query": {
                "keyword": keyword,
                "location": location,
                "country": country,
                "domain": domain,
                "date_posted_days": 30,
                "sort": "date",
                "sponsored_included": False,
            },
            # Number of jobs actually returned after filtering.
            "count": len(recent_jobs),
            # Provider estimate, not the count of relevant jobs.
            "provider_total_results": provider_total,
            "provider_page_count": len(provider_jobs),
            "jobs": recent_jobs,
        }


indeed_job_service = IndeedJobService()
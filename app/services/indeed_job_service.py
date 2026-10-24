
import json
import logging
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
    """Could not complete or interpret the Indeed search."""


def infer_domain(
    country: str | None,
    location: str | None,
) -> str | None:
    """Infer an Indeed domain from an explicit country or location."""
    country_text = (country or "").strip().lower()
    location_text = (location or "").strip().lower()

    normalized_country = COUNTRY_ALIASES.get(
        country_text,
        country_text,
    )

    if normalized_country in COUNTRY_DOMAINS:
        return COUNTRY_DOMAINS[normalized_country]

    # Prefer longer names to avoid matching a short alias inside another word.
    combined = f"{country_text} {location_text}"

    for name in sorted(COUNTRY_DOMAINS, key=len, reverse=True):
        if name in combined:
            return COUNTRY_DOMAINS[name]

    for alias, canonical in COUNTRY_ALIASES.items():
        if country_text == alias:
            return COUNTRY_DOMAINS[canonical]

    # Do not silently force unknown countries to the US domain.
    return None


def parse_provider_response(raw: Any) -> Any:
    """Decode JSON returned as text, when possible."""
    if isinstance(raw, (dict, list)):
        return raw

    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"raw_text": raw}

    content = getattr(raw, "content", None)

    if isinstance(content, str):
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"raw_text": content}

    if isinstance(content, list):
        text_parts: list[str] = []

        for block in content:
            if isinstance(block, dict):
                text_value = block.get("text")
                if text_value:
                    text_parts.append(text_value)
            elif isinstance(block, str):
                text_parts.append(block)
            else:
                text_value = getattr(block, "text", None)
                if text_value:
                    text_parts.append(text_value)

        combined = "\n".join(text_parts)

        if combined:
            try:
                return json.loads(combined)
            except json.JSONDecodeError:
                return {"raw_text": combined}

    return {"raw_text": str(raw)}


def extract_jobs(payload: Any) -> list[dict[str, Any]] | None:
    """
    Return a list only for recognized job-result structures.
    None means the response format is not recognized.
    """
    if isinstance(payload, list):
        if all(isinstance(item, dict) for item in payload):
            # An empty list can represent a valid empty result.
            return payload
        return None

    if not isinstance(payload, dict):
        return None

    # Common provider response formats.
    for key in ("jobs", "results"):
        value = payload.get(key)

        if isinstance(value, list):
            if all(isinstance(item, dict) for item in value):
                return value
            return None

    # "data" is accepted only if it clearly contains job results.
    data = payload.get("data")
    if isinstance(data, list):
        if all(isinstance(item, dict) for item in data):
            if not data or any(
                any(
                    field in item
                    for field in ("title", "jobTitle", "job_title")
                )
                for item in data
            ):
                return data

    nested = payload.get("json")
    if isinstance(nested, (dict, list)):
        return extract_jobs(nested)

    # A provider may explicitly report an empty result.
    if payload.get("jobs") == [] or payload.get("results") == []:
        return []

    return None


class IndeedJobService:
    async def search_jobs(
        self,
        *,
        keyword: str,
        location: str,
        country: str | None = None,
        date_posted: int | None = None,
    ) -> dict[str, Any]:
        keyword = keyword.strip()
        location = location.strip()

        if not keyword:
            raise ValueError("Job keyword cannot be empty.")

        if not location:
            raise ValueError("Job location cannot be empty.")

        domain = infer_domain(country, location)

        try:
            raw_result = await indeed_mcp_client.search_jobs(
                keyword=keyword,
                location=location,
                domain=domain,
                date_posted=date_posted,
            )
        except IndeedMCPError:
            # Preserve MCP errors so the API layer can map them to HTTP errors.
            raise
        except Exception as exc:
            logger.exception("Unexpected error during Indeed search.")
            raise IndeedJobSearchError(
                "Unable to complete the Indeed job search."
            ) from exc

        payload = parse_provider_response(raw_result)
        jobs = extract_jobs(payload)

        if jobs is None:
            logger.error(
                "Unrecognized Indeed response. Response type: %s",
                type(payload).__name__,
            )
            raise IndeedJobSearchError(
                "The provider returned an unrecognized response format."
            )

        return {
            "status": "success",
            "query": {
                "keyword": keyword,
                "location": location,
                "country": country,
                "domain": domain,
                "date_posted": date_posted,
            },
            "count": len(jobs),
            "jobs": jobs,
        }


indeed_job_service = IndeedJobService()
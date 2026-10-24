
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemes.indeed_jobs import (
    IndeedJobSearchRequest,
    IndeedJobSearchResponse,
)
from app.services.indeed_job_service import (
    indeed_job_service,
    IndeedJobSearchError,
)
from app.services.indeed_mcp_client import (
    IndeedMCPConfigurationError,
    IndeedMCPConnectionError,
    IndeedMCPToolError,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/jobs/indeed",
    tags=["Indeed Jobs"],
)


@router.post(
    "/search",
    response_model=IndeedJobSearchResponse,
    status_code=status.HTTP_200_OK,
)
async def search_indeed_jobs(
    request: IndeedJobSearchRequest,
):
    """
    Search Indeed jobs through the HasData MCP integration.
    """
    try:
        result = await indeed_job_service.search_jobs(
            keyword=request.keyword,
            location=request.location,
            country=request.country,
            date_posted=request.date_posted,
        )

        return result

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    except IndeedMCPConfigurationError as exc:
        logger.error("Indeed MCP configuration error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Indeed job search is not configured correctly.",
        ) from exc

    except IndeedMCPConnectionError as exc:
        logger.warning("Indeed MCP connection error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="The Indeed job search provider is unavailable or timed out.",
        ) from exc

    except IndeedMCPToolError as exc:
        logger.warning("Indeed MCP tool error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The Indeed provider could not complete the search.",
        ) from exc

    except IndeedJobSearchError as exc:
        logger.warning("Indeed search error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not process the Indeed search results.",
        ) from exc

    except Exception as exc:
        logger.exception("Unexpected error in Indeed search route.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while searching for jobs.",
        ) from exc

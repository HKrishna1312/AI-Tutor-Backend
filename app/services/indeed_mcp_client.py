
import asyncio
import logging
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient

from app.core.config import settings

logger = logging.getLogger(__name__)

LISTING_TOOL = "hasdata_indeed_listing_getJobListings"


class IndeedMCPError(Exception):
    """Base exception for Indeed MCP errors."""


class IndeedMCPConfigurationError(IndeedMCPError):
    """Missing MCP configuration."""


class IndeedMCPConnectionError(IndeedMCPError):
    """Could not connect to the MCP server."""


class IndeedMCPToolError(IndeedMCPError):
    """The Indeed listing tool failed."""


class IndeedMCPClient:
    def __init__(self) -> None:
        self._client: MultiServerMCPClient | None = None
        self._listing_tool: Any | None = None
        self._lock = asyncio.Lock()

    def _create_client(self) -> MultiServerMCPClient:
        url = (settings.INDEED_MCP_URL or "").strip()
        api_key = (settings.HASDATA_API_KEY or "").strip()

        if not url:
            raise IndeedMCPConfigurationError(
                "INDEED_MCP_URL is not configured."
            )

        if not api_key:
            raise IndeedMCPConfigurationError(
                "HASDATA_API_KEY is not configured."
            )

        return MultiServerMCPClient(
            {
                "indeed": {
                    "transport": "streamable_http",
                    "url": url,
                    "headers": {
                        "x-api-key": api_key,
                    },
                }
            }
        )

    async def initialize(self) -> None:
        """Connect and discover the Indeed listing tool once."""
        async with self._lock:
            if self._listing_tool is not None:
                return

            try:
                client = self._create_client()

                tools = await asyncio.wait_for(
                    client.get_tools(),
                    timeout=30,
                )

                listing_tool = next(
                    (
                        tool
                        for tool in tools
                        if tool.name == LISTING_TOOL
                    ),
                    None,
                )

                if listing_tool is None:
                    available = [tool.name for tool in tools]
                    logger.error(
                        "Indeed listing tool not found. Available tools: %s",
                        available,
                    )
                    raise IndeedMCPToolError(
                        "The Indeed listing tool was not found."
                    )

                # Keep the original tool and its schema intact.
                self._client = client
                self._listing_tool = listing_tool

                logger.info("Indeed MCP connected successfully.")

                logger.debug(
                    "Indeed listing tool input schema: %s",
                    listing_tool.get_input_schema().model_json_schema(),
                )

            except IndeedMCPError:
                raise
            except asyncio.TimeoutError as exc:
                raise IndeedMCPConnectionError(
                    "Timed out while connecting to Indeed MCP."
                ) from exc
            except Exception as exc:
                logger.exception("Indeed MCP initialization failed.")
                raise IndeedMCPConnectionError(
                    "Could not initialize Indeed MCP."
                ) from exc

    async def search_jobs(self,*,
    keyword: str,
    location: str,
    domain: str | None = None,
    date_posted: int | None = None,
) -> Any:
            keyword = keyword.strip()
            location = location.strip()

            if not keyword or not location:
                raise ValueError("keyword and location are required.")

            await self.initialize()

            if self._listing_tool is None:
                raise IndeedMCPToolError("Indeed listing tool is not initialized.")

            schema = self._listing_tool.get_input_schema().model_json_schema()
            properties = schema.get("properties", {})

            arguments: dict[str, Any] = {
                "keyword": keyword,
                "location": location,
            }

            # Pass the India domain when the tool supports it.
            if domain and "domain" in properties:
                arguments["domain"] = domain

            # Prefer newest listings.
            if "sort" in properties:
                arguments["sort"] = "date"

            # Use the provider's date filter only if exposed by its tool schema.
            if date_posted is not None and "datePosted" in properties:
                arguments["datePosted"] = date_posted

            logger.info(
                "Indeed search: keyword=%r location=%r domain=%r",
                keyword,
                location,
                domain,
            )
            logger.debug("Indeed tool argument keys: %s", list(arguments.keys()))

            try:
                return await asyncio.wait_for(
                    self._listing_tool.ainvoke(arguments),
                    timeout=45,
                )
            except asyncio.TimeoutError as exc:
                raise IndeedMCPConnectionError(
                    "Indeed search timed out."
                ) from exc
            except Exception as exc:
                logger.exception("Indeed listing tool execution failed.")
                raise IndeedMCPToolError(
                    f"Indeed listing tool execution failed: {exc}"
                ) from exc

    async def close(self) -> None:
        """Clear cached references."""
        async with self._lock:
            self._listing_tool = None
            self._client = None


indeed_mcp_client = IndeedMCPClient()

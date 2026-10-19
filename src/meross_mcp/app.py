"""Main application entrypoint and Dual Gateway aggregator (FastAPI + FastMCP)."""

import argparse
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from meross_mcp.api import router as api_router
from meross_mcp.client import MerossClientManager
from meross_mcp.config import MerossSettings
from meross_mcp.server import mcp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("meross_mcp")


def create_app(settings: MerossSettings | None = None) -> FastAPI:
    """Create and configure the unified FastAPI Dual Gateway application."""
    app_settings = settings or MerossSettings()
    mcp_app = mcp.http_app(path="/mcp")

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        """Application lifespan context manager for startup and shutdown hooks."""
        logger.info("Initializing Meross Dual Gateway on %s:%d...", app_settings.host, app_settings.port)

        # Pre-warm connection if credentials are configured
        if app_settings.email and app_settings.password:
            try:
                client = await MerossClientManager.get_instance(app_settings)
                await client.connect()
            except Exception as e:
                logger.warning("Initial connection to Meross Cloud postponed or failed: %s", e)

        # Drive FastMCP's StreamableHTTPSessionManager task group lifespan
        async with mcp_app.lifespan(app):
            yield

        # Graceful shutdown: close persistent MQTT connections and log out
        logger.info("Shutting down Meross Dual Gateway...")
        try:
            client = await MerossClientManager.get_instance(app_settings)
            await client.close()
        except Exception as e:
            logger.warning("Error during graceful shutdown: %s", e)

    app = FastAPI(
        title="Meross Dual Gateway",
        description=(
            "Unified Model Context Protocol (MCP) server & REST API Gateway for Meross smart plugs. "
            "Provides interactive OpenAPI documentation and real-time MQTT device control."
        ),
        version="0.1.2",
        lifespan=lifespan,
    )
    app.state.settings = app_settings

    # Enable CORS for dashboard and browser interactions
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check probe
    @app.get("/healthz", tags=["System"], summary="Health check probe")
    async def healthz() -> dict[str, str]:
        return {"status": "ok", "service": "meross-mcp"}

    # Include REST API routes (/api/v1/devices)
    app.include_router(api_router)

    # Mount FastMCP application directly so /mcp matches without redirect
    app.mount("", mcp_app)

    return app


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    settings = MerossSettings()
    parser = argparse.ArgumentParser(
        description="Meross Dual Gateway: Model Context Protocol (MCP) & REST API Server"
    )
    parser.add_argument(
        "--transport",
        choices=["http", "stdio"],
        default="http",
        help="Transport mode: 'http' for Dual Gateway (REST + MCP on HTTP/SSE), 'stdio' for AI CLI pipes (default: http)",
    )
    parser.add_argument(
        "--host",
        default=settings.host,
        help=f"Bind host for the HTTP server (default: {settings.host})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=settings.port,
        help=f"Bind port for the HTTP server (default: {settings.port})",
    )
    return parser.parse_args()


def main() -> None:
    """Console script entrypoint."""
    args = parse_args()

    if args.transport == "stdio":
        logger.info("Starting Meross MCP server in stdio transport mode...")
        # Run FastMCP directly in stdio mode
        mcp.run(transport="stdio")
    else:
        settings = MerossSettings(host=args.host, port=args.port)
        app = create_app(settings)
        logger.info(
            "Starting Meross Dual Gateway at http://%s:%d (Docs: /docs, MCP: /mcp)...",
            args.host,
            args.port,
        )
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()

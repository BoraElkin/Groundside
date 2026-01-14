"""
Ground Operations Intelligence Platform - FastAPI Application Entry Point
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog
from typing import Dict, List
import json
from datetime import datetime

from config import settings
from models.database import engine, Base
from api.routes import flights, turnarounds, alerts, analytics, customers
from api.metering import MeteringMiddleware


# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()


# WebSocket connection manager for real-time updates
class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept and store a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("websocket_connected", total_connections=len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        self.active_connections.remove(websocket)
        logger.info("websocket_disconnected", total_connections=len(self.active_connections))

    async def broadcast(self, message: Dict):
        """Broadcast a message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error("websocket_broadcast_error", error=str(e))
                disconnected.append(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)


manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("application_startup", environment=settings.environment)

    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("database_tables_created")

    yield

    # Shutdown
    logger.info("application_shutdown")


# Create FastAPI application
app = FastAPI(
    title="Ground Operations Intelligence Platform",
    description="AI-powered platform for predicting and preventing aircraft turnaround delays",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add API metering middleware
app.add_middleware(MeteringMiddleware)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "timestamp": datetime.utcnow().isoformat(),
        "airport": settings.default_airport_code,
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Ground Operations Intelligence Platform",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "api_prefix": settings.api_v1_prefix,
    }


# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time turnaround and alert updates.

    Clients can subscribe to real-time updates for:
    - Turnaround status changes
    - New alerts
    - Flight updates
    - Delay predictions
    """
    await manager.connect(websocket)
    try:
        while True:
            # Receive messages from client (e.g., subscriptions)
            data = await websocket.receive_text()
            message = json.loads(data)

            # Echo back confirmation
            await websocket.send_json({
                "type": "subscription_confirmed",
                "data": message,
                "timestamp": datetime.utcnow().isoformat()
            })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("client_disconnected")
    except Exception as e:
        logger.error("websocket_error", error=str(e))
        manager.disconnect(websocket)


# Include API routers
app.include_router(
    flights.router,
    prefix=f"{settings.api_v1_prefix}/flights",
    tags=["flights"]
)

app.include_router(
    turnarounds.router,
    prefix=f"{settings.api_v1_prefix}/turnarounds",
    tags=["turnarounds"]
)

app.include_router(
    alerts.router,
    prefix=f"{settings.api_v1_prefix}/alerts",
    tags=["alerts"]
)

app.include_router(
    analytics.router,
    prefix=f"{settings.api_v1_prefix}/analytics",
    tags=["analytics"]
)

app.include_router(
    customers.router,
    prefix=f"{settings.api_v1_prefix}/customers",
    tags=["customers"]
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        method=request.method,
        error=str(exc)
    )
    return {
        "error": "Internal server error",
        "message": str(exc) if settings.debug else "An error occurred"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )

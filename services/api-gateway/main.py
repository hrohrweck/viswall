from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import asyncio
import os
import time

from routers import auth, instances, users, firewall, mail, metrics, routing, audit, vpn, firewall_simulation, assistant, groupware
from shared.database import init_db, get_db
from shared.models import Base
from metrics_collector import start_metrics_collector

# Prometheus metrics
try:
    from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

    http_requests_total = Counter(
        "http_requests_total",
        "Total HTTP requests",
        ["method", "endpoint", "status"],
    )
    http_request_duration_seconds = Histogram(
        "http_request_duration_seconds",
        "HTTP request duration",
        ["method", "endpoint"],
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

token_auth = HTTPBearer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    collector_task = start_metrics_collector()
    yield
    # Shutdown
    if collector_task is not None:
        collector_task.cancel()
        try:
            await collector_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="Viswall API Gateway",
    description="Central management API for distributed viswall instances",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def prometheus_metrics_middleware(request: Request, call_next):
    if not PROMETHEUS_AVAILABLE:
        return await call_next(request)

    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    # Skip metrics endpoint itself to avoid recursion
    if request.url.path == "/metrics":
        return response

    method = request.method
    endpoint = request.url.path
    status = str(response.status_code)

    http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(
        duration
    )

    return response


@app.get("/metrics", tags=["Monitoring"])
async def prometheus_metrics():
    if not PROMETHEUS_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prometheus client not installed",
        )
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(instances.router, prefix="/api/v1/instances", tags=["Instances"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(firewall.router, prefix="/api/v1/firewall", tags=["Firewall"])
app.include_router(routing.router, prefix="/api/v1/routing", tags=["Routing"])
app.include_router(mail.router, prefix="/api/v1/mail", tags=["Mail"])
app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["Metrics"])
app.include_router(audit.router, prefix="/api/v1/audit", tags=["Audit"])
app.include_router(vpn.router, prefix="/api/v1/vpn", tags=["VPN"])
app.include_router(
    firewall_simulation.router,
    prefix="/api/v1/simulation",
    tags=["Firewall Simulation"],
)
app.include_router(assistant.router, prefix="/api/v1/assistant", tags=["LLM Assistant"])
app.include_router(
    groupware.router, prefix="/api/v1/groupware", tags=["Groupware"]
)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": "viswall-api-gateway"}


@app.get("/api/v1/")
async def api_info():
    return {
        "name": "Viswall API Gateway",
        "version": "2.0.0",
        "features": [
            "multi-instance-management",
            "firewall-management",
            "firewall-rule-simulation",
            "firewall-test-suites",
            "llm-configuration-assistant",
            "mail-management",
            "metrics-collection",
            "rbac",
            "vpn-management-wireguard-ipsec-openvpn-l2tp-pptp",
            "site-to-site-vpn",
            "split-tunneling",
        ],
    }

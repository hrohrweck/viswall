from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import os

from .routers import auth, instances, users, firewall, mail, metrics, routing, audit, vpn, firewall_simulation
from shared.database import init_db, get_db
from shared.models import Base

token_auth = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown

app = FastAPI(
    title="Viswall API Gateway",
    description="Central management API for distributed viswall instances",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
app.include_router(firewall_simulation.router, prefix="/api/v1/simulation", tags=["Firewall Simulation"])

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
            "mail-management",
            "metrics-collection",
            "rbac",
            "vpn-management-wireguard-ipsec-openvpn-l2tp-pptp",
            "site-to-site-vpn",
            "split-tunneling"
        ]
    }

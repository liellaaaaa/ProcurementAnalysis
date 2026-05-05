from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ProcurementAnalysis API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
from backend.api.routes import products, prices, scrapers, analytics, reports, alerts

# Include routers
app.include_router(products.router)
app.include_router(prices.router)
app.include_router(scrapers.router)
app.include_router(analytics.router)
app.include_router(reports.router)
app.include_router(alerts.router)

@app.get("/")
async def root():
    return {"message": "ProcurementAnalysis API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    from config import API_HOST, API_PORT
    uvicorn.run(app, host=API_HOST, port=API_PORT)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os

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
from backend.api.routes import products, prices, scrapers, analytics, reports, alerts, categories, operation_logs

# Include routers (必须放在 catch-all 路由之前)
app.include_router(products.router)
app.include_router(prices.router)
app.include_router(scrapers.router)
app.include_router(analytics.router)
app.include_router(reports.router)
app.include_router(alerts.router)
app.include_router(categories.router)
app.include_router(operation_logs.router)

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIST = os.path.join(BASE_DIR, "frontend", "dist")


@app.get("/")
async def serve_index():
    """托管前端页面"""
    index_path = os.path.join(FRONTEND_DIST, "index.html")
    return FileResponse(index_path)


@app.get("/{path:path}")
async def serve_static(path: str):
    """托管前端静态资源"""
    # 跳过 API 路由
    if path.startswith("api"):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not Found")
    file_path = os.path.join(FRONTEND_DIST, path)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    # SPA fallback
    return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))

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
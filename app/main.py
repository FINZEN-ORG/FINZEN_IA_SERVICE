from fastapi import FastAPI

from app.api.routes import router as api_router


app = FastAPI(title="FINZEN IA Service", version="0.1.0")


@app.get("/", tags=["root"])
async def read_root():
    return {"message": "FINZEN IA Service: OK"}


# include API routers
app.include_router(api_router)

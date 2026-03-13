from fastapi import APIRouter

from app.api.routes.company_esg import router as company_esg_router


api_router = APIRouter()
api_router.include_router(company_esg_router)
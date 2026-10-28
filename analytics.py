"""Analytics API endpoint providing datasets for Chart.js dashboards."""
from fastapi import APIRouter
from ..models import AnalyticsSummary
from ..services.analytics_service import analytics_service

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("", response_model=AnalyticsSummary)
def get_analytics():
    """Retrieve full analytics summary and Chart.js formatted datasets."""
    return analytics_service.get_summary()

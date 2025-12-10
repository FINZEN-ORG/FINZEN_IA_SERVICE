import httpx
from config import settings

async def get_user_goals(user_id: int):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{settings.GOALS_SERVICE_URL}/goals")
            return response.json() if response.status_code == 200 else []
        except Exception as e:
            print(f"Error fetching goals: {e}")
            return []
import httpx
from config import settings

async def get_user_transactions(user_id: int):
    # En un entorno real, aquí deberías pasar un token de servicio o propagar el del usuario.
    # Por ahora asumimos que los microservicios confían en la red interna o usas un token maestro.
    async with httpx.AsyncClient() as client:
        # Llamamos al endpoint de reporte o lista
        try:
            # Simulamos llamada. Ajusta la ruta a tu endpoint real de /transactions
            # Necesitamos un endpoint que devuelva JSON, no DTOs Java serializados raros.
            response = await client.get(
                f"{settings.TRANSACTIONS_SERVICE_URL}/transactions",
                headers={"X-User-Id": str(user_id)} # O el header que uses
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Error fetching transactions: {e}")
            return []

async def get_financial_summary(user_id: int):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.TRANSACTIONS_SERVICE_URL}/transactions/reports",
                headers={"X-User-Id": str(user_id)} # O el header que uses
            )
            return response.json() if response.status_code == 200 else {}
        except Exception as e:
            print(f"Error fetching transactions reports: {e}")
            return []
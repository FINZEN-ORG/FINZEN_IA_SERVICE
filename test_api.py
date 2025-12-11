"""
Script de testing para FinZen IA Service
Ejecuta: python test_api.py
"""

import requests
import json
from datetime import datetime

# CONFIGURACIÓN
BASE_URL = "http://localhost:8084"
# Obtén un token real de tu microservicio de Users
JWT_TOKEN = "Bearer eyJhbGciOiJSUz..."  # Reemplazar con token real

def test_health():
    """Test 1: Health check"""
    print("\nTest 1: Health Check")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    print("Health check passed")

def test_financial_analysis():
    """Test 2: Análisis financiero general"""
    print("\nTest 2: Análisis Financiero")
    
    payload = {
        "user_id": 1,
        "user_query": "analiza mi salud financiera",
        "context": "friendly"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": JWT_TOKEN
    }
    
    response = requests.post(
        f"{BASE_URL}/analyze",
        json=payload,
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Action: {data.get('action')}")
        print(f"Message: {data.get('message')}")
        print(f"Data keys: {list(data.get('data', {}).keys())}")
        print("Financial analysis passed")
    else:
        print(f"Error: {response.text}")

def test_ant_expenses():
    """Test 3: Detección de gastos hormiga"""
    print("\nTest 3: Gastos Hormiga")
    
    payload = {
        "user_id": 1,
        "user_query": "analiza mis gastos hormiga",
        "context": "friendly"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": JWT_TOKEN
    }
    
    response = requests.post(
        f"{BASE_URL}/analyze",
        json=payload,
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        ant_expenses = data.get('data', {}).get('ant_expenses', [])
        print(f"Gastos hormiga detectados: {len(ant_expenses)}")
        if ant_expenses:
            print(f"Ejemplo: {ant_expenses[0]}")
        print(" Ant expenses analysis passed")
    else:
        print(f" Error: {response.text}")

def test_goal_suggestions():
    """Test 4: Sugerencias de metas"""
    print("\n Test 4: Sugerencias de Metas")
    
    payload = {
        "user_id": 1,
        "user_query": "sugiere nuevas metas financieras",
        "context": "friendly"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": JWT_TOKEN
    }
    
    response = requests.post(
        f"{BASE_URL}/analyze",
        json=payload,
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        suggestions = data.get('data', {}).get('suggested_goals', [])
        print(f"Metas sugeridas: {len(suggestions)}")
        for goal in suggestions:
            print(f"  - {goal.get('name')}: ${goal.get('estimated_target')}")
        print(" Goal suggestions passed")
    else:
        print(f"Error: {response.text}")

def test_goal_tracking():
    """Test 5: Seguimiento de metas"""
    print("\n Test 5: Seguimiento de Metas")
    
    payload = {
        "user_id": 1,
        "user_query": "muestra el progreso de mis metas",
        "context": "friendly"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": JWT_TOKEN
    }
    
    response = requests.post(
        f"{BASE_URL}/analyze",
        json=payload,
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        goals_status = data.get('data', {}).get('goals_status', [])
        print(f"Metas rastreadas: {len(goals_status)}")
        for goal in goals_status:
            print(f"  - {goal.get('name')}: {goal.get('progress_percentage')}% completado")
        print(" Goal tracking passed")
    else:
        print(f" Error: {response.text}")

def test_with_manual_data():
    """Test 6: Con datos manuales (sin llamar a otros microservicios)"""
    print("\n Test 6: Análisis con datos manuales")
    
    payload = {
        "user_id": 1,
        "user_query": "analiza mi situación",
        "context": "friendly",
        "transactions": [
            {
                "id": 1,
                "amount": 50000,
                "description": "Mercado",
                "date": "2025-12-01T10:00:00",
                "type": "EXPENSE",
                "category_id": 1
            },
            {
                "id": 2,
                "amount": 3000,
                "description": "Café",
                "date": "2025-12-02T08:00:00",
                "type": "EXPENSE",
                "category_id": 2
            }
        ],
        "goals": [
            {
                "id": 1,
                "name": "Viaje a Cartagena",
                "target_amount": 2000000,
                "saved_amount": 500000,
                "category": "TRAVEL",
                "due_date": "2026-06-01",
                "status": "ACTIVE"
            }
        ],
        "financial_context": {
            "monthly_income": 3000000,
            "fixed_expenses": 1500000,
            "variable_expenses": 800000,
            "savings": 200000,
            "month_surplus": 700000
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": JWT_TOKEN
    }
    
    response = requests.post(
        f"{BASE_URL}/analyze",
        json=payload,
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Message: {data.get('message')}")
        print(f"Health Score: {data.get('data', {}).get('health_score', 'N/A')}")
        print(" Manual data analysis passed")
    else:
        print(f" Error: {response.text}")

def main():
    """Ejecuta todos los tests"""
    print("=" * 50)
    print(" FinZen IA Service - Test Suite")
    print("=" * 50)
    
    try:
        test_health()
        
        test_financial_analysis()
        test_ant_expenses()
        test_goal_suggestions()
        test_goal_tracking()
        test_with_manual_data()
        
        print("\n" + "=" * 50)
        print(" All tests completed!")
        print("=" * 50)
        
    except Exception as e:
        print("Test suite failed")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
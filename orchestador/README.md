# 🎯 Smart Wallet Orchestrator Agent

[![NestJS](https://img.shields.io/badge/NestJS-E0234E?style=for-the-badge&logo=nestjs&logoColor=white)](https://nestjs.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![AWS](https://img.shields.io/badge/AWS-232F3E?style=for-the-badge&logo=amazon-aws&logoColor=white)](https://aws.amazon.com/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)

> **Orchestrator Agent** para Smart Wallet - Sistema de orquestación inteligente que coordina agentes especializados de IA para gestión financiera personal.

---

## 📋 Descripción

El **Orchestrator Agent** es el cerebro central del ecosistema Smart Wallet. Recibe eventos del CoreSystem, consulta memoria contextual (episódica y semántica), decide qué agente especializado debe procesar cada evento, y coordina la comunicación asíncrona mediante AWS SQS.

### 🎯 Responsabilidades

- ✅ Recibir eventos del CoreSystem (transacciones, metas, presupuestos)
- ✅ Consultar memoria unificada en PostgreSQL (Episódica + Semántica + Transacciones + Metas)
- ✅ Decidir flujo con LangGraph basado en tipo de evento
- ✅ Publicar mensajes a colas SQS específicas por agente
- ✅ Generar correlation IDs para trazabilidad end-to-end

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                     CoreSystem (Java)                        │
│              (Transacciones, Metas, Presupuestos)            │
└──────────────────────┬──────────────────────────────────────┘
                       │ POST /events
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                  Orchestrator Agent (NestJS)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │  PostgreSQL  │  │  PostgreSQL  │  │   LangGraph      │    │
│  │ (Episódica)  │  │  (Semántica) │  │   (Decisión)     │    │
│  └──────────────┘  └──────────────┘  └──────────────────┘    │
└──────────────────────┬──────────────────────────────────────┘
                       │ Publish to SQS
         ┌─────────────┼─────────────┬─────────────┐
         ↓             ↓             ↓             ↓
┌─────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│ Financial   │ │  Goals   │ │  Budget  │ │ Motivational │
│  Insight    │ │  Agent   │ │ Balancer │ │    Coach     │
│   Agent     │ │ (Python) │ │ (Make)   │ │   (Make)     │
│ (Node.js)   │ │          │ │          │ │              │
└─────────────┘ └──────────┘ └──────────┘ └──────────────┘
```

---

## � API y Flujo de Mensajes

El endpoint principal es `POST /events`. El orquestador recibe el evento, enriquece el contexto consultando las bases de datos PostgreSQL, y envía un mensaje enriquecido a la cola SQS del agente correspondiente.

### **Estructura General del Mensaje SQS**

Todos los agentes reciben un mensaje con esta estructura unificada:

```json
{
  "event": {
    // El payload original recibido en /events
    "userId": "1",
    "type": "EVENT_TYPE",
    "data": { ... }
  },
  "context": {
    // Contexto enriquecido desde PostgreSQL
    "episodic": [ ... ],       // Últimos 100 eventos del usuario
    "semantic": { ... },       // Perfil financiero y motivacional
    "transactions": [ ... ],   // Últimas 20 transacciones
    "goals": [ ... ]           // Metas y presupuestos activos
  },
  "timestamp": "2023-10-27T10:00:00.000Z"
}
```

### **1. Financial Insight Agent**
**Cola:** `SQS_FINANCIAL_INSIGHT_QUEUE_URL`
**Eventos:** `NEW_TRANSACTION`, `TRANSACTION_UPDATED`, `ANOMALY_DETECTION_REQUEST`, `FINANCIAL_SUMMARY_REQUEST`, `ANT_EXPENSES_PROMPT`, `REPETITIVE_EXPENSES_PROMPT`, `HEALTH_PROMPT`, `LEAKS_PROMPT`, `FULL_ANALYSIS_PROMPT`

**Ejemplos de Input (`POST /events`):**

#### Detectar Gastos Hormiga
```json
{
  "userId": "123",
  "type": "ANT_EXPENSES_PROMPT",
  "data": {}
}
```

#### Análisis de Salud Financiera
```json
{
  "userId": "123",
  "type": "HEALTH_PROMPT",
  "data": {}
}
```

#### Análisis Completo
```json
{
  "userId": "123",
  "type": "FULL_ANALYSIS_PROMPT",
  "data": {}
}
```

### **2. Goals Agent**
**Cola:** `SQS_GOALS_QUEUE_URL`
**Eventos:** `GOAL_DISCOVERY_REQUEST`, `GOAL_VIABILITY_CHECK`, `GOAL_ADJUSTMENT_REQUEST`, `GOAL_PROGRESS_UPDATE`

**Ejemplos de Input (`POST /events`):**

#### Descubrimiento de Metas
```json
{
  "userId": "123",
  "type": "GOAL_DISCOVERY_REQUEST",
  "data": {}
}
```

#### Evaluar Viabilidad de Nueva Meta
```json
{
  "userId": "123",
  "type": "GOAL_VIABILITY_CHECK",
  "data": {
    "proposed_goal": {
      "name": "Comprar Laptop",
      "target_amount": 1500000,
      "due_date": "2026-06-01",
      "description": "Laptop para trabajo"
    }
  }
}
```

#### Ajuste de Metas (Rebalanceo)
```json
{
  "userId": "123",
  "type": "GOAL_ADJUSTMENT_REQUEST",
  "data": {}
}
```

#### Seguimiento de Progreso
```json
{
  "userId": "123",
  "type": "GOAL_PROGRESS_UPDATE",
  "data": {
    "goalId": "8000"
  }
}
```

### **3. Budget Balancer Agent**
**Cola:** `SQS_BUDGET_BALANCER_QUEUE_URL`
**Eventos:** `BUDGET_UPDATE_REQUEST`, `BUDGET_REBALANCE`, `SPENDING_LIMIT_EXCEEDED`

**Ejemplo Input (`POST /events`):**
```json
{
  "userId": "1",
  "type": "SPENDING_LIMIT_EXCEEDED",
  "data": {
    "category": "Entertainment",
    "limit": 200,
    "currentSpending": 250
  }
}
```

### **4. Motivational Coach Agent**
**Cola:** `SQS_MOTIVATIONAL_COACH_QUEUE_URL`
**Eventos:** `GOAL_PROGRESS_UPDATE`, `MILESTONE_REACHED`, `MOTIVATION_REQUEST`, `GOAL_REJECTED`

**Ejemplo Input (`POST /events`):**
```json
{
  "userId": "1",
  "type": "MILESTONE_REACHED",
  "data": {
    "goalId": "101",
    "milestone": "Saved first $1000",
    "message": "Great job on hitting your first milestone!"
  }
}
```

## �🚀 Inicio Rápido

### **Prerrequisitos**

- Node.js 20+ LTS
- AWS CLI (opcional, para AWS real)
- Cuenta AWS con SQS (o usar LocalStack para testing local)
- Bases de datos PostgreSQL (Railway)

### **Instalación**

```bash
# Clonar repositorio
git clone <repo-url>
cd orchestrator

# Instalar dependencias
npm install

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales de AWS y PostgreSQL

# Modo desarrollo (hot reload)
|------------|-----------|-----------|
| **Framework** | NestJS 11 | Arquitectura modular y escalable |
| **Lenguaje** | TypeScript 5 | Type safety y mejor DX |
| **Orquestación** | LangGraph | Decisión de flujos (futuro: con LLM) |
| **Mensajería** | AWS SQS | Comunicación asíncrona con agentes |
| **Memoria Episódica** | PostgreSQL | Trazabilidad de acciones de agentes |
| **Memoria Semántica** | PostgreSQL | Contexto general del usuario |
| **Config** | @nestjs/config | Variables de entorno |

---

## 🔐 Seguridad

- ✅ Credenciales AWS via variables de entorno (nunca en código)
- ✅ IAM roles con least privilege
- ✅ Validación de inputs en controllers
- ✅ `.env` en `.gitignore` (nunca commitear secretos)

---

## 📊 Monitoreo

### **Logs**

Los logs incluyen correlation ID para trazabilidad:

```
[EventsService] Processing event: NEW_TRANSACTION for user123
[LangGraphService] Decided agent: financial-insight
[SqsService] Message sent to queue: financial-insight-queue
```

### **Métricas AWS CloudWatch**

- `ApproximateNumberOfMessagesVisible` - Mensajes pendientes en SQS
- `NumberOfMessagesSent` - Mensajes enviados
- `ApproximateAgeOfOldestMessage` - Edad del mensaje más antiguo

---

## 🚢 Despliegue

### **Docker**

```bash
# Build imagen
docker build -t orchestrator:latest .

# Run container
docker run -p 3000:3000 --env-file .env orchestrator:latest
```

### **AWS ECS (Producción)**

1. Push imagen a ECR
2. Crear ECS Task Definition
3. Configurar Service con auto-scaling
4. Variables de entorno via AWS Secrets Manager

---

## 🐛 Troubleshooting

### **Error: "AWS.SimpleQueueService.NonExistentQueue"**

**Causa**: La URL de la cola SQS no coincide con el nombre real en AWS.

**Solución**:
```bash
# 1. Listar tus colas reales
aws sqs list-queues --region us-east-1

# 2. Copiar las URLs EXACTAS a tu .env
# Ejemplo de salida:
# "https://sqs.us-east-1.amazonaws.com/905418183802/smartwallet-goals-queue"

# 3. Verificar que .env tenga las URLs correctas
cat .env | grep SQS
```

### **Error: "UnrecognizedClientException: The security token included in the request is invalid"**

**Causa**: Credenciales AWS inválidas o expiradas.

**Solución**:
```bash
# 1. Verificar credenciales
aws sts get-caller-identity

[SqsService] Sending to queue URL: https://sqs...
```

---

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama: `git checkout -b feature/nueva-funcionalidad`
3. Commit cambios: `git commit -m 'Add: nueva funcionalidad'`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es parte del ecosistema Smart Wallet.

---

## 👥 Equipo

Desarrollado con ❤️ por el equipo de Smart Wallet

---

## 📚 Documentación Adicional

- [Mapeo de Eventos](./docs/event-mapping.md)
- [Arquitectura Completa](./docs/architecture.md)

---

**¿Preguntas?** Abre un issue en GitHub o contacta al equipo de desarrollo.

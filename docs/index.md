---
layout: default
title: Cita.me
---

<p align="center">
  <h1 align="center">Cita.me</h1>
  <h3 align="center">Sistema Distribuido de Reserva de Citas Medicas</h3>
  <p align="center"><em>Proyecto academico - Sistemas Distribuidos y Programacion Concurrente</em></p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.110-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Next.js-14-000000?style=for-the-badge&logo=nextdotjs&logoColor=white" alt="Next.js">
  <img src="https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white" alt="Redis">
  <img src="https://img.shields.io/badge/RabbitMQ-3-FF6600?style=for-the-badge&logo=rabbitmq&logoColor=white" alt="RabbitMQ">
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
</p>

---

## Demo (local)

- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000
- **Swagger**: http://localhost:8000/docs
- **DB Viewer**: http://localhost:8080
- **Redis Commander**: http://localhost:8081

---

## Descripcion

**Cita.me** es una plataforma web para el agendamiento de citas medicas, construida como **sistema distribuido** con arquitectura orientada a servicios. Permite gestionar **pacientes**, **doctores**, **horarios** y **reservas**, con roles diferenciados.

El proyecto aplica en conjunto los siguientes conceptos:

| Concepto | Implementacion |
|---|---|
| Sistemas distribuidos | Multiples servicios orquestados con Docker Compose |
| Programacion concurrente | Locking distribuido con Redis para reservas simultaneas |
| APIs REST | Backend con FastAPI y documentacion Swagger automatica |
| Cache distribuido | Redis para respuestas frecuentes y disponibilidad medica |
| Mensajeria asincrona | RabbitMQ para eventos desacoplados |
| Contenedores | Cada servicio corre en su propio contenedor Docker |

---

## Stack tecnologico

| Capa | Tecnologia | Rol |
|---|---|---|
| **Backend** | Python - FastAPI | API REST + logica de negocio |
| **ORM** | SQLAlchemy (async) | Acceso a base de datos |
| **Frontend** | Next.js 14 - React | Interfaz de usuario |
| **Estilos** | Tailwind CSS | Diseno responsivo |
| **Cache / Lock** | Redis 7 | Cache + locking distribuido |
| **Mensajeria** | RabbitMQ 3 | Cola de eventos asincronos |
| **Base de Datos** | SQLite (aiosqlite) | Persistencia de datos |
| **Contenedores** | Docker - Docker Compose | Orquestacion de servicios |

---

## Arquitectura

```
+--------------------------------------------------+
|                     USUARIO                       |
|              (Navegador Web / Movil)              |
+--------------------------------------------------+
                          |
                          v HTTP/HTTPS
+--------------------------------------------------+
|                   FRONTEND                        |
|         Next.js - React - Tailwind CSS            |
|                  Puerto: 3000                     |
+--------------------------------------------------+
                          |
                          v REST API (JSON)
+--------------------------------------------------+
|                   BACKEND                         |
|              FastAPI (Python)                     |
|                  Puerto: 8000                     |
|  +-----------+  +-----------+  +---------------+  |
|  |  Routers  |  | Services  |  |    Models     |  |
|  |  /citas   |  |cita_service|  |  SQLAlchemy   |  |
|  | /pacientes|  |validaciones|  |    ORM        |  |
|  | /doctores |  |  reglas   |  |   schemas     |  |
|  +-----------+  +-----------+  +---------------+  |
|  +---------------------------------------------+  |
|  |         Messaging (RabbitMQ)                |  |
|  |      Producer - Consumer - Events           |  |
|  +---------------------------------------------+  |
+--------------------------------------------------+
       |                    |                    |
       v Lock+Cache         v SQL                v AMQP
+-----------+      +----------------+      +-----------+
|   REDIS   |      |  BASE DE DATOS |      |  RABBITMQ |
|  Puerto   |      |     SQLite     |      |  Puerto   |
|   6379    |      |   citame.db    |      |   5672    |
| Cache +   |      |  pacientes     |      |  Colas de |
| Locking   |      |  doctores      |      |  eventos  |
|Distribuido|      |  horarios      |      |  asincrona|
|           |      |  citas         |      |           |
+-----------+      +----------------+      +-----------+
```

---

## Estructura del proyecto

```
Cita.me-2/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── redis_client.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── pacientes.py
│   │   ├── doctores.py
│   │   ├── horarios.py
│   │   ├── citas.py
│   │   ├── portal.py
│   │   └── doctor_portal.py
│   ├── services/
│   │   └── cita_service.py
│   ├── messaging/
│   │   ├── producer.py
│   │   └── consumer.py
│   ├── test_concurrencia.py
│   └── test_rabbitmq.py
├── frontend/
│   ├── src/app/
│   ├── src/components/
│   ├── src/hooks/
│   └── src/services/
├── db_viewer/
├── docker-compose.yml
└── README.md
```

---

## Funcionalidades

### Pacientes

- Registro de pacientes
- Consulta por ID
- Consulta por documento
- Historial de citas

### Doctores

- Registro de doctores
- Especialidades
- Consulta de agenda
- Portal medico

### Horarios

- Configuracion de disponibilidad
- Consulta de horarios por doctor

### Citas Medicas

- Crear cita
- Consultar cita
- Cancelar cita
- Confirmar cita
- Completar cita
- Ver citas por paciente
- Ver citas por doctor

### Portales

- Portal del paciente
- Portal del doctor
- Portal del Administrador
- Inicio de sesion por rol

---

## Endpoints de la API

Para el detalle completo y ejemplos, usa Swagger: http://localhost:8000/docs

### Generales

| Metodo | Endpoint |
|--------|----------|
| GET    | /        |
| GET    | /health  |

### Auth

| Metodo | Endpoint             |
|--------|----------------------|
| POST   | /auth/login          |
| GET    | /auth/doctores-lista |

### Pacientes

| Metodo | Endpoint                         |
|--------|----------------------------------|
| POST   | /pacientes/                      |
| GET    | /pacientes/                      |
| GET    | /pacientes/{id}                  |
| GET    | /pacientes/documento/{documento} |

### Doctores

| Metodo | Endpoint         |
|--------|------------------|
| POST   | /doctores/       |
| GET    | /doctores/       |
| GET    | /doctores/{id}   |

### Horarios

| Metodo | Endpoint                      |
|--------|-------------------------------|
| POST   | /horarios/                    |
| GET    | /horarios/doctor/{doctor_id}  |

### Citas

| Metodo | Endpoint                          |
|--------|-----------------------------------|
| POST   | /citas/                           |
| GET    | /citas/                           |
| GET    | /citas/{id}                       |
| GET    | /citas/paciente/{paciente_id}     |
| GET    | /citas/doctor/{doctor_id}         |
| GET    | /citas/disponibles/{doctor_id}    |
| PUT    | /citas/{id}/estado                |

### Portal Paciente

| Metodo | Endpoint                        |
|--------|---------------------------------|
| GET    | /portal/mis-citas               |
| POST   | /portal/pedir-cita              |
| PUT    | /portal/cancelar/{id}           |
| GET    | /portal/doctores-disponibles    |

### Portal Doctor

| Metodo | Endpoint                        |
|--------|---------------------------------|
| GET    | /doctor-portal/mis-citas        |
| GET    | /doctor-portal/cita/{id}        |
| PUT    | /doctor-portal/completar/{id}   |
| PUT    | /doctor-portal/confirmar/{id}   |

---

## Redis

Redis se utiliza para:

- Almacenar respuestas frecuentes en cache
- Mejorar tiempos de consulta
- Reducir carga de base de datos
- Cachear disponibilidad medica
- Locking distribuido para reservas concurrentes

## RabbitMQ

RabbitMQ se utiliza para:

- Eventos al crear citas
- Confirmaciones de citas
- Cambios de estado
- Comunicacion asincrona desacoplada entre componentes

---

## Instalacion Rapida

Requisitos: Docker + Docker Compose

```bash
git clone https://github.com/MLopezCamp/Cita.me-2.git
cd Cita.me-2
docker-compose up --build
```

---

## Servicios y Puertos (local)

| Servicio | URL |
|----------|-----|
| Frontend | http://localhost:3000 |
| Backend | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| DB Viewer | http://localhost:8080 |
| Redis Commander | http://localhost:8081 |
| RabbitMQ Management | http://localhost:15672 |

---

## Licencia

Proyecto academico y educativo.

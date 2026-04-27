<div align="center">

# Cita.me

### Sistema Distribuido de Reserva de Citas Médicas

*Proyecto académico · Sistemas Distribuidos y Programación Concurrente*

---

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![RabbitMQ](https://img.shields.io/badge/RabbitMQ-3-FF6600?style=for-the-badge&logo=rabbitmq&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)

</div>

---

## Tabla de contenidos

- [Demo](#demo)
- [Descripción](#descripción)
- [Stack tecnológico](#stack-tecnológico)
- [Arquitectura](#arquitectura)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Funcionalidades](#funcionalidades)
- [Endpoints de la API](#endpoints-de-la-api)
- [Instalación rápida (Docker)](#instalación-rápida-docker)
- [Servicios y puertos (local)](#servicios-y-puertos-local)
- [GitHub Pages (frontend estático)](#github-pages-frontend-estático)
- [Licencia](#licencia)

---

## Demo

- **Frontend (local)**: `http://localhost:3000`
- **Backend (local)**: `http://localhost:8000`
- **Swagger (local)**: `http://localhost:8000/docs`
- **Redis Commander (local)**: `http://localhost:8081`
- **DB Viewer (local)**: `http://localhost:8080`

> Tip: si publicas el frontend en GitHub Pages, agrega aquí el enlace a la demo.

---

## Descripción

**Cita.me** es una plataforma web para el agendamiento de citas médicas, construida como **sistema distribuido** con arquitectura orientada a servicios. Permite gestionar **pacientes**, **doctores**, **horarios** y **reservas**, con roles diferenciados.

El proyecto aplica en conjunto los siguientes conceptos:

| Concepto | Implementacion |
|---|---|
| Sistemas distribuidos | Múltiples servicios orquestados con Docker Compose |
| Programación concurrente | Locking distribuido con Redis para reservas simultáneas |
| APIs REST | Backend con FastAPI y documentación Swagger automática |
| Caché distribuido | Redis para respuestas frecuentes y disponibilidad médica |
| Mensajería asíncrona | RabbitMQ para eventos desacoplados |
| Contenedores | Cada servicio corre en su propio contenedor Docker |

---

## Stack tecnológico

<div align="center">

| Capa | Tecnologia | Rol |
|---|---|---|
| **Backend** | Python · FastAPI | API REST + lógica de negocio |
| **ORM** | SQLAlchemy (async) | Acceso a base de datos |
| **Frontend** | Next.js 14 · React | Interfaz de usuario |
| **Estilos** | Tailwind CSS | Diseño responsivo |
| **Cache / Lock** | Redis 7 | Cache + locking distribuido |
| **Mensajería** | RabbitMQ 3 | Cola de eventos asíncronos |
| **Base de Datos** | SQLite (aiosqlite) | Persistencia de datos |
| **Contenedores** | Docker · Docker Compose | Orquestación de servicios |

</div>

---

## Arquitectura

```mermaid
graph TD
    U([Usuario / Navegador])

    subgraph Frontend["Frontend  —  Next.js · React · Tailwind"]
        FE[Paginas & Componentes]
    end

    subgraph Backend["Backend  —  FastAPI · SQLAlchemy"]
        API[Routers REST]
        SVC[Servicios de Negocio]
        API --> SVC
    end

    subgraph Mensajeria["Mensajería  —  RabbitMQ"]
        MQ[(Cola de Eventos)]
    end

    subgraph Cache["Cache & Locking  —  Redis"]
        RD[(Redis)]
    end

    subgraph DB["Persistencia  —  SQLite"]
        BD[(citame.db)]
    end

    subgraph Observabilidad["Observabilidad"]
        DBV[DB Viewer · :8080]
        RC[Redis Commander · :8081]
        SW[Swagger UI · :8000/docs]
    end

    U -->|HTTP| FE
    FE -->|REST API| API
    SVC -->|pub/sub| MQ
    SVC -->|get/set/lock| RD
    SVC -->|ORM| BD
    DBV -.->|lectura| BD
    RC -.->|lectura| RD
    SW -.->|docs| API
```

---

## Estructura del proyecto

```text
Cita.me-2/
├── backend/
├── frontend/
├── db_viewer/
├── docker-compose.yml
└── README.md
```

---

## Funcionalidades

- **Pacientes**: registro, consulta por ID/documento, historial de citas
- **Doctores**: registro, especialidades, agenda y portal médico
- **Horarios**: configuración de disponibilidad y consulta por doctor
- **Citas médicas**: crear/consultar/cancelar, confirmar/completar, listados por paciente/doctor
- **Portales**: paciente / doctor / administrador, inicio de sesión por rol

---

## Endpoints de la API

> Para el detalle completo y ejemplos, usa Swagger: `http://localhost:8000/docs`.

### Generales

| Método | Endpoint |
|---|---|
| GET | `/` |
| GET | `/health` |

### Auth

| Método | Endpoint |
|---|---|
| POST | `/auth/login` |
| GET | `/auth/doctores-lista` |

### Recursos principales

- **Pacientes**: `/pacientes/*`
- **Doctores**: `/doctores/*`
- **Horarios**: `/horarios/*`
- **Citas**: `/citas/*`
- **Portal paciente**: `/portal/*`
- **Portal doctor**: `/doctor-portal/*`

---

## Instalación rápida (Docker)

Requisitos: **Docker** + **Docker Compose**

```bash
git clone https://github.com/MLopezCamp/Cita.me-2.git
cd Cita.me-2
docker-compose up --build
```

---

## Servicios y puertos (local)

| Servicio | URL |
|---|---|
| Frontend | `http://localhost:3000` |
| Backend | `http://localhost:8000` |
| Swagger | `http://localhost:8000/docs` |
| DB Viewer | `http://localhost:8080` |
| Redis Commander | `http://localhost:8081` |
| RabbitMQ Management | `http://localhost:15672` |

---

## Licencia

Proyecto académico y educativo.

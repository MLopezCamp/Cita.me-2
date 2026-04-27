<div align="center">

# Cita.me

### Sistema Distribuido de Reserva de Citas Medicas

*Proyecto academico · Sistemas Distribuidos y Programacion Concurrente*

---

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![RabbitMQ](https://img.shields.io/badge/RabbitMQ-3-FF6600?style=for-the-badge&logo=rabbitmq&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)

</div>

---

## Tabla de Contenidos

- [Descripcion](#descripcion)
- [Stack Tecnologico](#stack-tecnologico)
- [Arquitectura](#arquitectura)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Funcionalidades](#funcionalidades)
- [Endpoints de la API](#endpoints-de-la-api)
- [Componentes Clave](#componentes-clave)
- [Instalacion Rapida](#instalacion-rapida)
- [Servicios y Puertos](#servicios-y-puertos)

---

## Descripcion

**Cita.me** es una plataforma web para el agendamiento de citas medicas, construida como sistema distribuido con arquitectura orientada a servicios. Permite gestionar pacientes, doctores, horarios y reservas con roles diferenciados.

El proyecto aplica en conjunto los siguientes conceptos:

| Concepto | Implementacion |
|---|---|
| Sistemas Distribuidos | Multiples servicios orquestados con Docker Compose |
| Programacion Concurrente | Locking distribuido con Redis para reservas simultaneas |
| APIs REST | Backend con FastAPI y documentacion Swagger automatica |
| Cache Distribuido | Redis para respuestas frecuentes y disponibilidad medica |
| Mensajeria Asincrona | RabbitMQ para eventos desacoplados entre componentes |
| Contenedores | Cada servicio corre en su propio contenedor Docker |

---

## Stack Tecnologico

<div align="center">

| Capa | Tecnologia | Rol |
|---|---|---|
| **Backend** | Python · FastAPI | API REST + logica de negocio |
| **ORM** | SQLAlchemy (async) | Acceso a base de datos |
| **Frontend** | Next.js 14 · React | Interfaz de usuario |
| **Estilos** | Tailwind CSS | Diseno responsivo |
| **Cache / Lock** | Redis 7 | Cache + locking distribuido |
| **Mensajeria** | RabbitMQ 3 | Cola de eventos asincronos |
| **Base de Datos** | SQLite (aiosqlite) | Persistencia de datos |
| **Contenedores** | Docker · Docker Compose | Orquestacion de servicios |

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

    subgraph Mensajeria["Mensajeria  —  RabbitMQ"]
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
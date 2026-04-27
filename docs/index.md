---
layout: default
title: Cita.me
---

<div align="center">

# Cita.me

### Sistema Distribuido de Reserva de Citas Médicas

*Proyecto académico · Sistemas Distribuidos y Programación Concurrente*

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![RabbitMQ](https://img.shields.io/badge/RabbitMQ-3-FF6600?style=for-the-badge&logo=rabbitmq&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)

</div>

---

## Demo (local)

- **Frontend**: `http://localhost:3000`
- **Backend**: `http://localhost:8000`
- **Swagger**: `http://localhost:8000/docs`
- **DB Viewer**: `http://localhost:8080`
- **Redis Commander**: `http://localhost:8081`

---

## Descripción

**Cita.me** es una plataforma web para el agendamiento de citas médicas, construida como **sistema distribuido** con arquitectura orientada a servicios. Permite gestionar **pacientes**, **doctores**, **horarios** y **reservas**, con roles diferenciados.

---

## Arquitectura

> Nota: si tu GitHub Pages no soporta Mermaid, el diagrama puede no renderizar. En ese caso, se verá igual en el `README.md` del repo.

```mermaid
flowchart TD
  FE[Frontend - Next.js] -->|HTTP| API[Backend - FastAPI]
  API --> DB[(SQLite)]
  API --> R[(Redis: cache + locking)]
  API --> MQ[(RabbitMQ: eventos)]
```

---

## Instalación rápida (Docker)

```bash
docker-compose up --build
```

---




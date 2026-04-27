# Cita.me - Sistema Distribuido de Reserva de Citas Medica

Sistema distribuido de agendamiento de citas médicas desarrollado con arquitectura moderna basada en servicios. El proyecto integra backend escalable con FastAPI, frontend en Next.js, base de datos relacional, Redis para caché, RabbitMQ para mensajería asíncrona y Docker Compose para orquestación local.

---

## Resumen

Cita.me Redis permite administrar pacientes, doctores, horarios disponibles y reservas de citas médicas mediante una plataforma web con roles diferenciados.

El sistema fue diseñado aplicando conceptos de:

- Sistemas distribuidos
- Programación concurrente
- APIs REST
- Cache distribuido
- Mensajería entre servicios
- Despliegue con contenedores

---

## Stack Tecnológico

| Área | Tecnología |
|---|---|
| Backend | Python, FastAPI |
| ORM | SQLAlchemy |
| Frontend | Next.js, React |
| Estilos | Tailwind CSS |
| Cache | Redis |
| Mensajería | RabbitMQ |
| Base de Datos | SQL |
| Contenedores | Docker, Docker Compose |

---

## Arquitectura General

```text
Frontend Next.js
      |
      v
FastAPI Backend
 |      |      |
 |      |      └── RabbitMQ
 |      |
 |      └── Redis Cache
 |
 └── Base de Datos SQLite
```

---

## Estructura del Proyecto

```text
cita.me-redis/
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
│
├── frontend/
│   ├── src/app/
│   ├── src/components/
│   ├── src/hooks/
│   └── src/services/
│
├── db_viewer/
├── docker-compose.yml
└── README.md
```

---

## Funcionalidades Principales

### Pacientes

- Registro de pacientes
- Consulta por ID
- Consulta por documento
- Historial de citas

### Doctores

- Registro de doctores
- Especialidades
- Consulta de agenda
- Portal médico

### Horarios

- Configuración de disponibilidad
- Consulta de horarios por doctor

### Citas Médicas

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
- Inicio de sesión por rol

---

## Endpoints de la API

## Generales

| Método | Endpoint |
|---|---|
| GET | / |
| GET | /health |

## Auth

| Método | Endpoint |
|---|---|
| POST | /auth/login |
| GET | /auth/doctores-lista |

## Pacientes

| Método | Endpoint |
|---|---|
| POST | /pacientes/ |
| GET | /pacientes/ |
| GET | /pacientes/{id} |
| GET | /pacientes/documento/{documento} |

## Doctores

| Método | Endpoint |
|---|---|
| POST | /doctores/ |
| GET | /doctores/ |
| GET | /doctores/{id} |

## Horarios

| Método | Endpoint |
|---|---|
| POST | /horarios/ |
| GET | /horarios/doctor/{doctor_id} |

## Citas

| Método | Endpoint |
|---|---|
| POST | /citas/ |
| GET | /citas/ |
| GET | /citas/{id} |
| GET | /citas/paciente/{paciente_id} |
| GET | /citas/doctor/{doctor_id} |
| GET | /citas/disponibles/{doctor_id} |
| PUT | /citas/{id}/estado |

## Portal Paciente

| Método | Endpoint |
|---|---|
| GET | /portal/mis-citas |
| POST | /portal/pedir-cita |
| PUT | /portal/cancelar/{id} |
| GET | /portal/doctores-disponibles |

## Portal Doctor

| Método | Endpoint |
|---|---|
| GET | /doctor-portal/mis-citas |
| GET | /doctor-portal/cita/{id} |
| PUT | /doctor-portal/completar/{id} |
| PUT | /doctor-portal/confirmar/{id} |

---

## Redis

Redis se utiliza para:

- Almacenar respuestas frecuentes
- Mejorar tiempos de consulta
- Reducir carga de base de datos
- Cachear disponibilidad médica

---

## RabbitMQ

RabbitMQ se utiliza para:

- Eventos al crear citas
- Confirmaciones
- Cambios de estado
- Comunicación desacoplada

---

## Instalación Rápida

```bash
git clone https://github.com/MLopezCamp/Cita.me-2.git
cd cita.me-redis
docker-compose up --build
```

---

## Acceso Local

| Servicio | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |

---

## Licencia

Proyecto académico y educativo.

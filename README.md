# Cita.me - Sistema Distribuido de Reserva de Citas Medicas

Sistema distribuido de agendamiento de citas medicas desarrollado con arquitectura basada en servicios. El proyecto integra backend con FastAPI (Python), frontend en Next.js, base de datos relacional, Redis para cache y locking distribuido, RabbitMQ para mensajeria asincrona, y Docker Compose para orquestacion local.

---

## Resumen

Cita.me permite administrar pacientes, doctores, horarios disponibles y reservas de citas medicas mediante una plataforma web con roles diferenciados.

El sistema fue disenado aplicando conceptos de:

- Sistemas distribuidos
- Programacion concurrente
- APIs REST
- Cache distribuido
- Locking distribuido con Redis
- Mensajeria asincrona con RabbitMQ
- Despliegue con contenedores

---

## Stack Tecnologico

| Area         | Tecnologia      |
|--------------|-----------------|
| Backend      | Python, FastAPI |
| ORM          | SQLAlchemy      |
| Frontend     | Next.js, React  |
| Estilos      | Tailwind CSS    |
| Cache / Lock | Redis           |
| Mensajeria   | RabbitMQ        |
| Base de Datos| SQLite          |
| Contenedores | Docker, Docker Compose |

---

## Arquitectura General

```
Frontend Next.js
      |
      v
FastAPI Backend
 |      |      |
 |      |      └── RabbitMQ (eventos asincronos)
 |      |
 |      └── Redis (cache + locking distribuido)
 |
 └── Base de Datos SQLite
```

---

## Estructura del Proyecto

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

```bash
git clone https://github.com/MLopezCamp/Cita.me-2.git
cd Cita.me-2
docker-compose up --build
```

---

## Acceso Local

| Servicio | URL                          |
|----------|------------------------------|
| Frontend | http://localhost:3000        |
| Backend  | http://localhost:8000        |
| Swagger  | http://localhost:8000/docs   |
| Redis Commander | http://localhost:8081  |
---

## Licencia

Proyecto academico y educativo.

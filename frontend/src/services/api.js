const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Rutas que NO necesitan token (públicas)
const PUBLIC_ENDPOINTS = ["/auth/login", "/auth/doctores-lista", "/health"];

function getToken() {
  try {
    const stored = localStorage.getItem("citame_user");
    if (!stored) return null;
    const parsed = JSON.parse(stored);
    return parsed.access_token || null;
  } catch {
    return null;
  }
}

async function request(endpoint, options = {}) {
  const url = `${API_URL}${endpoint}`;

  const isPublic = PUBLIC_ENDPOINTS.some((pub) => endpoint.startsWith(pub));
  const token = isPublic ? null : getToken();

  const config = {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
    ...options,
  };

  const response = await fetch(url, config);

  // Token expirado o inválido → limpiar sesión y redirigir al login
  if (response.status === 401) {
    localStorage.removeItem("citame_user");
    window.location.href = "/login";
    throw new Error("Sesión expirada. Por favor inicie sesión nuevamente.");
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Error ${response.status}`);
  }

  return response.json();
}

export const pacientes = {
  crear: (data) => request("/pacientes/", { method: "POST", body: JSON.stringify(data) }),
  listar: () => request("/pacientes/"),
  obtener: (id) => request(`/pacientes/${id}`),
  actualizar: (id, data) => request(`/pacientes/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  eliminar: (id) => request(`/pacientes/${id}`, { method: "DELETE" }),
};

export const doctores = {
  crear: (data) => request("/doctores/", { method: "POST", body: JSON.stringify(data) }),
  listar: () => request("/doctores/"),
  obtener: (id) => request(`/doctores/${id}`),
  toggleActivo: (id) => request(`/doctores/${id}/activo`, { method: "PUT" }),
  eliminar: (id) => request(`/doctores/${id}`, { method: "DELETE" }),
};

export const administrativos = {
  crear: (data) => request("/administrativos/", { method: "POST", body: JSON.stringify(data) }),
  listar: () => request("/administrativos/"),
  actualizar: (id, data) => request(`/administrativos/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  activar: (id) => request(`/administrativos/${id}/activar`, { method: "PATCH" }),
  eliminar: (id) => request(`/administrativos/${id}`, { method: "DELETE" }),
};

export const horarios = {
  crear: (data) => request("/horarios/", { method: "POST", body: JSON.stringify(data) }),
  crearLote: (data) => request("/horarios/lote", { method: "POST", body: JSON.stringify(data) }),
  porDoctor: (doctorId) => request(`/horarios/doctor/${doctorId}`),
  actualizar: (id, data) => request(`/horarios/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  desactivar: (id) => request(`/horarios/${id}`, { method: "DELETE" }),
};

export const citas = {
  crear: (data) => request("/citas/", { method: "POST", body: JSON.stringify(data) }),
  listar: () => request("/citas/"),
  obtener: (id) => request(`/citas/${id}`),
  disponibles: (doctorId, fecha) => request(`/citas/disponibles/${doctorId}?fecha=${fecha}`),
  actualizarEstado: (id, data) =>
    request(`/citas/${id}/estado`, { method: "PUT", body: JSON.stringify(data) }),
};

export const auth = {
  login: (data) => request("/auth/login", { method: "POST", body: JSON.stringify(data) }),
  doctoresLista: () => request("/auth/doctores-lista"),
  me: () => request("/auth/me"),
};

export const portal = {
  misCitas: () => request("/portal/mis-citas"),
  pedirCita: (data) => request("/portal/pedir-cita", { method: "POST", body: JSON.stringify(data) }),
  cancelarCita: (citaId) => request(`/portal/cancelar/${citaId}`, { method: "PUT" }),
  doctoresDisponibles: () => request("/portal/doctores-disponibles"),
};

export const doctorPortal = {
  misCitas: (estado) => request(`/doctor-portal/mis-citas?estado=${estado}`),
  confirmar: (citaId) => request(`/doctor-portal/confirmar/${citaId}`, { method: "PUT" }),
  obtenerCita: (citaId) => request(`/doctor-portal/cita/${citaId}`),
  completar: (citaId, notas) =>
    request(`/doctor-portal/completar/${citaId}?notas=${encodeURIComponent(notas)}`, {
      method: "PUT",
    }),
};

export const partesMedicos = {
  crear: (data) => request("/partes-medicos/", { method: "POST", body: JSON.stringify(data) }),
  porCita: (citaId) => request(`/partes-medicos/cita/${citaId}`),
};

export const health = () => request("/health");
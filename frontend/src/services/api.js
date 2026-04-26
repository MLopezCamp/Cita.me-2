const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request(endpoint, options = {}) {
  const url = `${API_URL}${endpoint}`;
  const config = {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  };
  const response = await fetch(url, config);
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
};

export const doctores = {
  crear: (data) => request("/doctores/", { method: "POST", body: JSON.stringify(data) }),
  listar: () => request("/doctores/"),
  obtener: (id) => request(`/doctores/${id}`),
};

export const horarios = {
  crear: (data) => request("/horarios/", { method: "POST", body: JSON.stringify(data) }),
  porDoctor: (doctorId) => request(`/horarios/doctor/${doctorId}`),
};

export const citas = {
  crear: (data) => request("/citas/", { method: "POST", body: JSON.stringify(data) }),
  listar: () => request("/citas/"),
  obtener: (id) => request(`/citas/${id}`),
  disponibles: (doctorId, fecha) => request(`/citas/disponibles/${doctorId}?fecha=${fecha}`),
  actualizarEstado: (id, data) => request(`/citas/${id}/estado`, { method: "PUT", body: JSON.stringify(data) }),
};

export const auth = {
  login: (data) => request("/auth/login", { method: "POST", body: JSON.stringify(data) }),
  doctoresLista: () => request("/auth/doctores-lista"),
};

export const portal = {
  misCitas: (pacienteId) => request(`/portal/mis-citas?paciente_id=${pacienteId}`),
  pedirCita: (data) => request("/portal/pedir-cita", { method: "POST", body: JSON.stringify(data) }),
  cancelarCita: (citaId, pacienteId) =>
    request(`/portal/cancelar/${citaId}?paciente_id=${pacienteId}`, { method: "PUT" }),
  doctoresDisponibles: () => request("/portal/doctores-disponibles"),
};

export const health = () => request("/health");
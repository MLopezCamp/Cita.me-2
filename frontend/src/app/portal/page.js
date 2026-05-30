"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { portal, partesMedicos } from "../../services/api";
import { useAuth } from "../../hooks/useAuth";
import StatusBadge from "../../components/StatusBadge";

export default function PortalPage() {
  const { user, loading: authLoading, logout } = useAuth("paciente");
  const [misCitas, setMisCitas] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [error, setError] = useState("");
  const [cancelando, setCancelando] = useState(null);
  const [parteAbierto, setParteAbierto] = useState(null);
  const [parteData, setParteData] = useState({});
  const [parteLoading, setParteLoading] = useState(false);

  useEffect(() => {
    if (!user) return;
    cargar();
  }, [user]);

  async function cargar() {
    try {
      // El backend extrae el paciente_id del JWT — no hace falta enviarlo en la URL
      const data = await portal.misCitas();
      setMisCitas(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setDataLoading(false);
    }
  }

  async function cancelarCita(citaId) {
    if (!confirm("¿Cancelar esta cita?")) return;
    setCancelando(citaId);
    setError("");
    try {
      await portal.cancelarCita(citaId);
      await cargar();
    } catch (err) {
      setError(err.message);
    } finally {
      setCancelando(null);
    }
  }

  async function verParte(citaId) {
    if (parteAbierto === citaId) { setParteAbierto(null); return; }
    setParteAbierto(citaId);
    if (parteData[citaId] !== undefined) return;
    setParteLoading(true);
    try {
      const p = await partesMedicos.porCita(citaId);
      setParteData((prev) => ({ ...prev, [citaId]: p }));
    } catch {
      setParteData((prev) => ({ ...prev, [citaId]: null }));
    } finally {
      setParteLoading(false);
    }
  }

  if (authLoading) return <div className="text-center py-12 text-gray-400">Cargando...</div>;

  const activas = misCitas.filter((c) => c.estado !== "cancelada" && c.estado !== "completada");
  const historial = misCitas.filter(
    (c) => c.estado === "cancelada" || c.estado === "completada"
  );

  return (
    <div className="max-w-3xl mx-auto">
      {/* Header */}
      <div className="bg-white rounded-2xl border border-gray-100 p-6 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-sky-100 flex items-center justify-center text-sky-700 font-bold text-lg">
              {user?.nombre?.[0]}
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">{user?.nombre}</h1>
              <p className="text-sm text-gray-500">Doc: {user?.documento}</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="px-4 py-2 text-sm text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
          >
            Salir
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      <Link
        href="/portal/nueva-cita"
        className="block bg-sky-600 hover:bg-sky-700 text-white rounded-xl p-5 mb-6 transition-colors group"
      >
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold">Pedir una nueva cita</h2>
            <p className="text-sky-100 text-sm mt-1">Seleccione doctor, fecha y horario</p>
          </div>
          <svg
            className="w-6 h-6 text-sky-200 group-hover:translate-x-1 transition-transform"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
          </svg>
        </div>
      </Link>

      {/* Citas activas */}
      <div className="mb-6">
        <h2 className="text-sm font-bold text-gray-500 uppercase mb-3">
          Citas Activas ({activas.length})
        </h2>
        {dataLoading ? (
          <div className="text-center py-8 text-gray-400">Cargando...</div>
        ) : activas.length === 0 ? (
          <div className="bg-white rounded-xl border border-gray-100 p-8 text-center text-gray-400">
            Sin citas activas
          </div>
        ) : (
          <div className="space-y-3">
            {activas.map((c) => (
              <div key={c.id} className="bg-white rounded-xl border border-gray-100 p-5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="text-center min-w-[70px]">
                      <p className="text-xs text-gray-400 uppercase">Fecha</p>
                      <p className="font-bold text-gray-800">{c.fecha}</p>
                    </div>
                    <div className="w-px h-10 bg-gray-100" />
                    <div className="text-center min-w-[50px]">
                      <p className="text-xs text-gray-400 uppercase">Hora</p>
                      <p className="font-bold text-gray-800">{c.hora}</p>
                    </div>
                    <div className="w-px h-10 bg-gray-100" />
                    <div>
                      <p className="text-sm font-medium text-gray-800">{c.doctor_nombre}</p>
                      <p className="text-xs text-gray-500">{c.doctor_especialidad}</p>
                      <p className="text-xs text-gray-400 mt-0.5">{c.motivo}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <StatusBadge estado={c.estado} />
                    <button
                      onClick={() => cancelarCita(c.id)}
                      disabled={cancelando === c.id}
                      className="px-3 py-1.5 text-xs font-medium text-red-700 bg-red-50 rounded-lg hover:bg-red-100 disabled:opacity-50"
                    >
                      {cancelando === c.id ? "..." : "Cancelar"}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Historial */}
      {historial.length > 0 && (
        <div>
          <h2 className="text-sm font-bold text-gray-500 uppercase mb-3">
            Historial ({historial.length})
          </h2>
          <div className="space-y-2">
            {historial.map((c) => (
              <div key={c.id} className="bg-gray-50 rounded-xl overflow-hidden">
                <div className="flex items-center justify-between text-sm p-4">
                  <span className="font-medium text-gray-600">
                    {c.fecha} — {c.hora} · {c.doctor_nombre}
                  </span>
                  <div className="flex items-center gap-2">
                    <StatusBadge estado={c.estado} />
                    {c.estado === "completada" && (
                      <button
                        onClick={() => verParte(c.id)}
                        className="text-xs text-sky-600 hover:text-sky-800 font-medium transition-colors"
                      >
                        {parteAbierto === c.id ? "Ocultar" : "Parte médico"}
                      </button>
                    )}
                  </div>
                </div>
                {parteAbierto === c.id && (
                  <div className="border-t border-gray-200 bg-white px-4 pb-4 pt-3 text-sm">
                    {parteLoading && parteData[c.id] === undefined ? (
                      <p className="text-gray-400">Cargando...</p>
                    ) : parteData[c.id] ? (
                      <div className="space-y-2">
                        <div>
                          <span className="text-xs font-semibold text-gray-400 uppercase">Diagnóstico</span>
                          <p className="text-gray-700 mt-0.5">{parteData[c.id].diagnostico}</p>
                        </div>
                        {parteData[c.id].tratamiento && (
                          <div>
                            <span className="text-xs font-semibold text-gray-400 uppercase">Tratamiento</span>
                            <p className="text-gray-700 mt-0.5">{parteData[c.id].tratamiento}</p>
                          </div>
                        )}
                        {parteData[c.id].observaciones && (
                          <div>
                            <span className="text-xs font-semibold text-gray-400 uppercase">Observaciones</span>
                            <p className="text-gray-700 mt-0.5">{parteData[c.id].observaciones}</p>
                          </div>
                        )}
                      </div>
                    ) : (
                      <p className="text-gray-400 italic">No hay parte médico registrado para esta cita.</p>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
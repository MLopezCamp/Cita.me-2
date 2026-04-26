"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { portal } from "../../services/api";
import { useAuth } from "../../hooks/useAuth";
import StatusBadge from "../../components/StatusBadge";

export default function PortalPage() {
  const { user, loading: authLoading, logout } = useAuth("paciente");
  const [misCitas, setMisCitas] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [error, setError] = useState("");
  const [cancelando, setCancelando] = useState(null);

  useEffect(() => {
    if (!user) return;
    async function cargar() {
      try {
        const data = await portal.misCitas(user.id);
        setMisCitas(data);
      } catch (err) { setError(err.message); }
      finally { setDataLoading(false); }
    }
    cargar();
  }, [user]);

  async function cancelarCita(citaId) {
    if (!confirm("¿Cancelar esta cita?")) return;
    setCancelando(citaId);
    setError("");
    try {
      await portal.cancelarCita(citaId, user.id);
      const data = await portal.misCitas(user.id);
      setMisCitas(data);
    } catch (err) { setError(err.message); }
    finally { setCancelando(null); }
  }

  if (authLoading) return <div className="text-center py-12 text-gray-400">Cargando...</div>;

  const activas = misCitas.filter((c) => c.estado !== "cancelada" && c.estado !== "completada");
  const historial = misCitas.filter((c) => c.estado === "cancelada" || c.estado === "completada");

  return (
    <div className="max-w-3xl mx-auto">
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
          <button onClick={logout} className="px-4 py-2 text-sm text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors">
            Salir
          </button>
        </div>
      </div>

      {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">{error}</div>}

      <Link href="/portal/nueva-cita"
        className="block bg-sky-600 hover:bg-sky-700 text-white rounded-xl p-5 mb-6 transition-colors group">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold">Pedir una nueva cita</h2>
            <p className="text-sky-100 text-sm mt-1">Seleccione doctor, fecha y horario</p>
          </div>
          <svg className="w-6 h-6 text-sky-200 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
          </svg>
        </div>
      </Link>

      <div className="mb-6">
        <h2 className="text-sm font-bold text-gray-500 uppercase mb-3">Citas Activas ({activas.length})</h2>
        {activas.length === 0 ? (
          <div className="bg-white rounded-xl border border-gray-100 p-8 text-center text-gray-400">Sin citas activas</div>
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
                    <button onClick={() => cancelarCita(c.id)} disabled={cancelando === c.id}
                      className="px-3 py-1.5 text-xs font-medium text-red-700 bg-red-50 rounded-lg hover:bg-red-100 disabled:opacity-50">
                      {cancelando === c.id ? "..." : "Cancelar"}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {historial.length > 0 && (
        <div>
          <h2 className="text-sm font-bold text-gray-500 uppercase mb-3">Historial ({historial.length})</h2>
          <div className="space-y-2">
            {historial.map((c) => (
              <div key={c.id} className="bg-gray-50 rounded-xl p-4 opacity-70">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium text-gray-600">{c.fecha} — {c.hora} · {c.doctor_nombre}</span>
                  <StatusBadge estado={c.estado} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
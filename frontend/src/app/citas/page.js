"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "../../hooks/useAuth";
import { citas } from "../../services/api";
import StatusBadge from "../../components/StatusBadge";

export default function CitasPage() {
  const { user, loading: authLoading } = useAuth("admin");
  const [lista, setLista] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [error, setError] = useState("");
  const [filtro, setFiltro] = useState("todas");

  useEffect(() => {
    if (!user) return;
    cargarCitas();
  }, [user]);

  async function cargarCitas() {
    try {
      const data = await citas.listar();
      setLista(data);
    } catch (err) { setError(err.message); }
    finally { setDataLoading(false); }
  }

  async function cambiarEstado(citaId, nuevoEstado) {
    try {
      await citas.actualizarEstado(citaId, { estado: nuevoEstado });
      await cargarCitas();
    } catch (err) { setError(err.message); }
  }

  const filtradas = filtro === "todas" ? lista : lista.filter((c) => c.estado === filtro);

  if (authLoading) return <div className="text-center py-12 text-gray-400">Cargando...</div>;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-extrabold text-gray-900">Citas</h1>
          <p className="text-sm text-gray-500">{lista.length} en total</p>
        </div>
        <Link href="/nueva-cita"
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-brand-600 text-white rounded-lg font-medium hover:bg-brand-700 transition-colors">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          Nueva Cita
        </Link>
      </div>

      {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">{error}</div>}

      <div className="flex gap-2 mb-5">
        {["todas", "pendiente", "confirmada", "cancelada", "completada"].map((f) => (
          <button key={f} onClick={() => setFiltro(f)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              filtro === f ? "bg-brand-600 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}>
            {f === "todas" ? "Todas" : f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {dataLoading ? (
        <div className="text-center py-12 text-gray-400">Cargando...</div>
      ) : filtradas.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-xl border border-gray-100">
          <p className="text-gray-400 text-lg">No hay citas</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtradas.map((c, i) => (
            <Link key={c.id} href={`/citas/${c.id}`}
              className="card-animate block bg-white rounded-xl border border-gray-100 p-5 hover:shadow-md hover:border-gray-200 transition-all"
              style={{ animationDelay: `${i * 40}ms` }}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="text-center">
                    <p className="text-xs text-gray-400 uppercase">Fecha</p>
                    <p className="font-bold text-gray-800">{c.fecha}</p>
                  </div>
                  <div className="w-px h-10 bg-gray-100" />
                  <div className="text-center">
                    <p className="text-xs text-gray-400 uppercase">Hora</p>
                    <p className="font-bold text-gray-800">{c.hora}</p>
                  </div>
                  <div className="w-px h-10 bg-gray-100" />
                  <div>
                    <p className="text-sm font-medium text-gray-800">Paciente #{c.paciente_id}</p>
                    <p className="text-sm text-gray-500">Doctor #{c.doctor_id}</p>
                    <p className="text-xs text-gray-400 mt-0.5">{c.motivo}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <StatusBadge estado={c.estado} />
                  {c.estado === "pendiente" && (
                    <button onClick={(e) => { e.preventDefault(); cambiarEstado(c.id, "confirmada"); }}
                      className="px-3 py-1.5 text-xs font-medium text-brand-700 bg-brand-50 rounded-lg hover:bg-brand-100 transition-colors">
                      Confirmar
                    </button>
                  )}
                  {c.estado !== "cancelada" && c.estado !== "completada" && (
                    <button onClick={(e) => { e.preventDefault(); cambiarEstado(c.id, "cancelada"); }}
                      className="px-3 py-1.5 text-xs font-medium text-red-700 bg-red-50 rounded-lg hover:bg-red-100 transition-colors">
                      Cancelar
                    </button>
                  )}
                  <svg className="w-4 h-4 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                  </svg>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
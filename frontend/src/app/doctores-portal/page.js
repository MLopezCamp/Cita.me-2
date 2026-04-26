"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "../../hooks/useAuth";
import StatusBadge from "../../components/StatusBadge";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchJSON(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || "Error");
  return r.json();
}

export default function DoctorPortalPage() {
  const { user, loading: authLoading, logout } = useAuth("doctor");
  const [citas, setCitas] = useState([]);
  const [filtro, setFiltro] = useState("pendiente");
  const [dataLoading, setDataLoading] = useState(true);
  const [error, setError] = useState("");
  const [confirmando, setConfirmando] = useState(null);

  useEffect(() => {
    if (!user) return;
    cargar();
  }, [user, filtro]);

  async function cargar() {
    setDataLoading(true);
    setError("");
    try {
      const data = await fetchJSON(`${API}/doctor-portal/mis-citas?doctor_id=${user.id}&estado=${filtro}`);
      setCitas(data);
    } catch (err) { setError(err.message); }
    finally { setDataLoading(false); }
  }

  async function confirmar(citaId) {
    setConfirmando(citaId);
    try {
      await fetch(`${API}/doctor-portal/confirmar/${citaId}?doctor_id=${user.id}`, { method: "PUT" });
      await cargar();
    } catch (err) { setError(err.message); }
    finally { setConfirmando(null); }
  }

  if (authLoading) return <div className="text-center py-12 text-gray-400">Cargando...</div>;

  const filtros = [
    { value: "pendiente", label: "Pendientes" },
    { value: "confirmada", label: "Confirmadas" },
    { value: "completada", label: "Completadas" },
    { value: "cancelada", label: "Canceladas" },
  ];

  return (
    <div className="max-w-3xl mx-auto">
      {/* Header */}
      <div className="bg-white rounded-2xl border border-gray-100 p-6 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-amber-100 flex items-center justify-center text-amber-700 font-bold text-lg">
              {user?.nombre?.[0]}
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">{user?.nombre}</h1>
              <p className="text-sm text-gray-500">{user?.especialidad}</p>
            </div>
          </div>
          <button onClick={logout} className="px-4 py-2 text-sm text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors">
            Salir
          </button>
        </div>
      </div>

      {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">{error}</div>}

      {/* Filtros */}
      <div className="flex gap-2 mb-5">
        {filtros.map((f) => (
          <button key={f.value} onClick={() => setFiltro(f.value)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              filtro === f.value ? "bg-amber-600 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}>
            {f.label}
          </button>
        ))}
      </div>

      {dataLoading ? (
        <div className="text-center py-12 text-gray-400">Cargando...</div>
      ) : citas.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-100 p-8 text-center text-gray-400">
          No hay citas {filtro !== "pendiente" ? `con estado "${filtro}"` : "pendientes"}
        </div>
      ) : (
        <div className="space-y-3">
          {citas.map((c) => (
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
                    <p className="text-sm font-medium text-gray-800">{c.paciente_nombre}</p>
                    <p className="text-xs text-gray-500">Doc: {c.paciente_documento}</p>
                    <p className="text-xs text-gray-400 mt-0.5">{c.motivo}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <StatusBadge estado={c.estado} />
                  {c.estado === "pendiente" && (
                    <button onClick={() => confirmar(c.id)} disabled={confirmando === c.id}
                      className="px-3 py-1.5 text-xs font-medium text-amber-700 bg-amber-50 rounded-lg hover:bg-amber-100 disabled:opacity-50">
                      {confirmando === c.id ? "..." : "Confirmar"}
                    </button>
                  )}
                  {c.estado === "confirmada" && (
                    <Link href={`/doctores-portal/cita/${c.id}`}
                      className="px-3 py-1.5 text-xs font-medium text-brand-700 bg-brand-50 rounded-lg hover:bg-brand-100">
                      Completar
                    </Link>
                  )}
                  {c.estado === "completada" && c.notas && (
                    <span className="text-xs text-gray-400 italic max-w-[150px] truncate block" title={c.notas}>
                      &quot;{c.notas}&quot;
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
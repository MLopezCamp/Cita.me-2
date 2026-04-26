"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "../../../hooks/useAuth";
import { citas } from "../../../services/api";
import StatusBadge from "../../../components/StatusBadge";

export default function CitaDetallePage() {
  const { id } = useParams();
  const router = useRouter();
  const { user, loading: authLoading } = useAuth("admin");

  const [cita, setCita] = useState(null);
  const [dataLoading, setDataLoading] = useState(true);
  const [error, setError] = useState("");
  const [nuevoEstado, setNuevoEstado] = useState("");
  const [notas, setNotas] = useState("");
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    if (!user) return;
    cargarCita();
  }, [user, id]);

  async function cargarCita() {
    setDataLoading(true);
    try {
      const data = await citas.obtener(id);
      setCita(data);
      setNuevoEstado(data.estado);
      setNotas(data.notas || "");
    } catch (err) {
      setError(err.message);
    }
    finally {
      setDataLoading(false);
    }
  }

  async function handleActualizar(e) {
    e.preventDefault();
    setEnviando(true);
    setError("");
    try {
      await citas.actualizarEstado(id, {
        estado: nuevoEstado,
        notas: notas || null,
      });
      await cargarCita();
    } catch (err) {
      setError(err.message);
    }
    finally {
      setEnviando(false);
    }
  }

  if (authLoading) {
    return <div className="text-center py-12 text-gray-400">Cargando...</div>;
  }

  if (!cita && !error) {
    return <div className="text-center py-12 text-gray-400">Cargando...</div>;
  }

  if (!cita) {
    return <div className="text-center py-12 text-red-500">{error}</div>;
  }

  return (
    <div className="max-w-2xl mx-auto">
      <button
        onClick={() => router.back()}
        className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-6 transition-colors"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
        </svg>
        Volver a Citas
      </button>

      <div className="bg-white rounded-2xl border border-gray-100 p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-xl font-extrabold text-gray-900">Cita #{cita.id}</h1>
          <StatusBadge estado={cita.estado} />
        </div>

        <div className="grid grid-cols-2 gap-y-4 gap-x-8 text-sm">
          <div>
            <p className="text-gray-400 text-xs uppercase mb-0.5">Fecha</p>
            <p className="font-semibold text-gray-800">{cita.fecha}</p>
          </div>
          <div>
            <p className="text-gray-400 text-xs uppercase mb-0.5">Hora</p>
            <p className="font-semibold text-gray-800">{cita.hora}</p>
          </div>
          <div>
            <p className="text-gray-400 text-xs uppercase mb-0.5">Paciente</p>
            <p className="font-semibold text-gray-800">
              {cita.paciente_nombre} {cita.paciente_apellido}
            </p>
            <p className="text-xs text-gray-500">ID: {cita.paciente_id}</p>
          </div>
          <div>
            <p className="text-gray-400 text-xs uppercase mb-0.5">Doctor</p>
            <p className="font-semibold text-gray-800">
              Dr. {cita.doctor_nombre} {cita.doctor_apellido}
            </p>
            <p className="text-xs text-gray-500">{cita.doctor_especialidad}</p>
          </div>
          <div className="col-span-2">
            <p className="text-gray-400 text-xs uppercase mb-0.5">Motivo</p>
            <p className="text-gray-800">{cita.motivo}</p>
          </div>
          {cita.notas && (
            <div className="col-span-2">
              <p className="text-gray-400 text-xs uppercase mb-0.5">Notas</p>
              <p className="text-gray-600">{cita.notas}</p>
            </div>
          )}
          <div>
            <p className="text-gray-400 text-xs uppercase mb-0.5">Creada</p>
            <p className="text-gray-500 text-xs">{cita.creado_en}</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-gray-100 p-6">
        <h2 className="text-lg font-bold text-gray-800 mb-4">Actualizar Cita</h2>
        <form onSubmit={handleActualizar} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Estado</label>
            <select
              value={nuevoEstado}
              onChange={(e) => setNuevoEstado(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
            >
              <option value="pendiente">Pendiente</option>
              <option value="confirmada">Confirmada</option>
              <option value="cancelada">Cancelada</option>
              <option value="completada">Completada</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Notas</label>
            <textarea
              value={notas}
              onChange={(e) => setNotas(e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent resize-none"
              placeholder="Agregar notas opcionales..."
            />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button
            type="submit"
            disabled={enviando}
            className="w-full py-2.5 bg-brand-600 text-white rounded-lg font-medium hover:bg-brand-700 transition-colors disabled:opacity-50"
          >
            {enviando ? "Actualizando..." : "Guardar Cambios"}
          </button>
        </form>
      </div>
    </div>
  );
}
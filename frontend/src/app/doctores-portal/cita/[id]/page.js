"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "../../../../hooks/useAuth";
import { doctorPortal } from "../../../../services/api";
import StatusBadge from "../../../../components/StatusBadge";

export default function DoctorCitaPage() {
  const { id } = useParams();
  const router = useRouter();
  const { user, loading: authLoading } = useAuth("doctor");
  const [cita, setCita] = useState(null);
  const [notas, setNotas] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState("");
  const [exito, setExito] = useState(false);

  useEffect(() => {
    if (!user) return;
    async function cargar() {
      try {
        const data = await doctorPortal.obtenerCita(id);
        setCita(data);
        setNotas(data.notas || "");
      } catch (err) {
        setError(err.message);
      }
    }
    cargar();
  }, [user, id]);

  async function handleCompletar(e) {
    e.preventDefault();
    setEnviando(true);
    setError("");
    try {
      await doctorPortal.completar(id, notas);
      setExito(true);
      setTimeout(() => router.push("/doctores-portal"), 1500);
    } catch (err) {
      setError(err.message);
    } finally {
      setEnviando(false);
    }
  }

  if (authLoading) return <div className="text-center py-12 text-gray-400">Cargando...</div>;

  if (exito) {
    return (
      <div className="max-w-lg mx-auto mt-20 text-center">
        <div className="w-16 h-16 rounded-full bg-brand-100 flex items-center justify-center mx-auto mb-4">
          <svg
            className="w-8 h-8 text-brand-600"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
          </svg>
        </div>
        <h2 className="text-xl font-bold text-gray-900 mb-1">Cita completada</h2>
        <p className="text-gray-500 text-sm">Redirigiendo...</p>
      </div>
    );
  }

  if (!cita && !error) return <div className="text-center py-12 text-gray-400">Cargando...</div>;

  return (
    <div className="max-w-lg mx-auto">
      <button
        onClick={() => router.back()}
        className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-6"
      >
        <svg
          className="w-4 h-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
        </svg>
        Volver
      </button>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      {cita && (
        <>
          <div className="bg-white rounded-2xl border border-gray-100 p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h1 className="text-lg font-bold text-gray-900">Cita #{cita.id}</h1>
              <StatusBadge estado={cita.estado} />
            </div>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Fecha y hora</span>
                <span className="font-medium text-gray-800">
                  {cita.fecha} — {cita.hora}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Paciente</span>
                <span className="font-medium text-gray-800">{cita.paciente_nombre}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Documento</span>
                <span className="font-medium text-gray-800">{cita.paciente_documento}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Teléfono</span>
                <span className="font-medium text-gray-800">{cita.paciente_telefono}</span>
              </div>
              <hr className="border-gray-100" />
              <div>
                <span className="text-gray-400 block mb-1">Motivo de consulta</span>
                <p className="text-gray-800">{cita.motivo}</p>
              </div>
              {cita.notas && (
                <div>
                  <span className="text-gray-400 block mb-1">Notas existentes</span>
                  <p className="text-gray-600 bg-gray-50 rounded-lg p-3">{cita.notas}</p>
                </div>
              )}
            </div>
          </div>

          {cita.estado === "confirmada" && (
            <div className="bg-white rounded-2xl border border-gray-100 p-6">
              <h2 className="text-lg font-bold text-gray-800 mb-1">Completar cita</h2>
              <p className="text-sm text-gray-500 mb-4">Agregue comentarios sobre la consulta</p>
              <form onSubmit={handleCompletar} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Comentarios / Diagnóstico
                  </label>
                  <textarea
                    value={notas}
                    onChange={(e) => setNotas(e.target.value)}
                    rows={5}
                    className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent resize-none"
                    placeholder="Describa el resultado de la consulta, diagnóstico, indicaciones..."
                  />
                </div>
                <button
                  type="submit"
                  disabled={enviando || !notas.trim()}
                  className="w-full py-3 bg-amber-600 text-white rounded-lg font-semibold hover:bg-amber-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {enviando ? "Guardando..." : "Marcar como Completada"}
                </button>
              </form>
            </div>
          )}

          {cita.estado === "completada" && (
            <div className="bg-brand-50 border border-brand-200 rounded-xl p-6 text-center">
              <p className="text-brand-700 font-medium">Esta cita ya fue completada</p>
              {cita.notas && (
                <p className="text-brand-600 text-sm mt-2">&quot;{cita.notas}&quot;</p>
              )}
            </div>
          )}

          {cita.estado === "cancelada" && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
              <p className="text-red-700 font-medium">Esta cita fue cancelada</p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
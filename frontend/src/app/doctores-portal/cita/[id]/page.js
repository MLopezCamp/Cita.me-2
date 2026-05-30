"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "../../../../hooks/useAuth";
import { doctorPortal, partesMedicos } from "../../../../services/api";
import StatusBadge from "../../../../components/StatusBadge";

export default function DoctorCitaPage() {
  const { id } = useParams();
  const router = useRouter();
  const { user, loading: authLoading } = useAuth("doctor");
  const [cita, setCita] = useState(null);
  const [parte, setParte] = useState(null);
  const [parteLoading, setParteLoading] = useState(false);
  const [notas, setNotas] = useState("");
  const [parteForm, setParteForm] = useState({ diagnostico: "", tratamiento: "", observaciones: "" });
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!user) return;
    cargar();
  }, [user, id]);

  async function cargar() {
    try {
      const data = await doctorPortal.obtenerCita(id);
      setCita(data);
      setNotas(data.notas || "");
      if (data.estado === "completada") {
        await cargarParte();
      }
    } catch (err) {
      setError(err.message);
    }
  }

  async function cargarParte() {
    setParteLoading(true);
    try {
      const p = await partesMedicos.porCita(id);
      setParte(p);
    } catch {
      // 404 significa que aun no hay parte, es esperado
      setParte(null);
    } finally {
      setParteLoading(false);
    }
  }

  async function handleCompletar(e) {
    e.preventDefault();
    setEnviando(true);
    setError("");
    try {
      await doctorPortal.completar(id, notas);
      // Recargar la cita para mostrar el formulario de parte medico
      const data = await doctorPortal.obtenerCita(id);
      setCita(data);
      setNotas(data.notas || "");
      setParte(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setEnviando(false);
    }
  }

  async function handleCrearParte(e) {
    e.preventDefault();
    setEnviando(true);
    setError("");
    try {
      const nuevo = await partesMedicos.crear({ cita_id: parseInt(id), ...parteForm });
      setParte(nuevo);
    } catch (err) {
      setError(err.message);
    } finally {
      setEnviando(false);
    }
  }

  function handleParteChange(e) {
    setParteForm({ ...parteForm, [e.target.name]: e.target.value });
  }

  const inputClass = "w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent";
  const textareaClass = "w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent resize-none";

  if (authLoading) return <div className="text-center py-12 text-gray-400">Cargando...</div>;
  if (!cita && !error) return <div className="text-center py-12 text-gray-400">Cargando...</div>;

  return (
    <div className="max-w-lg mx-auto">
      <button
        onClick={() => router.back()}
        className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-6"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
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
                <span className="font-medium text-gray-800">{cita.fecha} — {cita.hora}</span>
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
                  <span className="text-gray-400 block mb-1">Notas</span>
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
                    Comentarios / Notas
                  </label>
                  <textarea
                    value={notas}
                    onChange={(e) => setNotas(e.target.value)}
                    rows={4}
                    className={textareaClass.replace("brand-500", "amber-500")}
                    placeholder="Observaciones generales de la consulta..."
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
            parteLoading ? (
              <div className="text-center py-8 text-gray-400 text-sm">Cargando parte medico...</div>
            ) : parte ? (
              <div className="bg-white rounded-2xl border border-gray-100 p-6">
                <h2 className="text-lg font-bold text-gray-800 mb-4">Parte médico registrado</h2>
                <div className="space-y-3 text-sm">
                  <div>
                    <span className="text-gray-400 block mb-1 font-medium">Diagnóstico</span>
                    <p className="text-gray-700 bg-gray-50 rounded-lg p-3">{parte.diagnostico}</p>
                  </div>
                  {parte.tratamiento && (
                    <div>
                      <span className="text-gray-400 block mb-1 font-medium">Tratamiento</span>
                      <p className="text-gray-700 bg-gray-50 rounded-lg p-3">{parte.tratamiento}</p>
                    </div>
                  )}
                  {parte.observaciones && (
                    <div>
                      <span className="text-gray-400 block mb-1 font-medium">Observaciones</span>
                      <p className="text-gray-700 bg-gray-50 rounded-lg p-3">{parte.observaciones}</p>
                    </div>
                  )}
                </div>
                <button
                  onClick={() => router.push("/doctores-portal")}
                  className="mt-5 w-full py-2.5 bg-brand-600 text-white rounded-lg font-medium hover:bg-brand-700 transition-colors"
                >
                  Volver al portal
                </button>
              </div>
            ) : (
              <div className="bg-white rounded-2xl border border-brand-100 p-6">
                <div className="flex items-center gap-2 mb-1">
                  <div className="w-2 h-2 rounded-full bg-brand-500"></div>
                  <h2 className="text-lg font-bold text-gray-800">Registrar parte médico</h2>
                </div>
                <p className="text-sm text-gray-500 mb-5">
                  La cita fue completada. Complete el parte médico para finalizar el proceso.
                </p>
                <form onSubmit={handleCrearParte} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Diagnóstico <span className="text-red-400">*</span>
                    </label>
                    <textarea
                      name="diagnostico"
                      value={parteForm.diagnostico}
                      onChange={handleParteChange}
                      required
                      rows={3}
                      className={textareaClass}
                      placeholder="Diagnóstico del paciente..."
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Tratamiento</label>
                    <textarea
                      name="tratamiento"
                      value={parteForm.tratamiento}
                      onChange={handleParteChange}
                      rows={3}
                      className={textareaClass}
                      placeholder="Tratamiento indicado (opcional)..."
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Observaciones</label>
                    <textarea
                      name="observaciones"
                      value={parteForm.observaciones}
                      onChange={handleParteChange}
                      rows={2}
                      className={textareaClass}
                      placeholder="Observaciones adicionales (opcional)..."
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={enviando || !parteForm.diagnostico.trim()}
                    className="w-full py-3 bg-brand-600 text-white rounded-lg font-semibold hover:bg-brand-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {enviando ? "Guardando..." : "Guardar parte médico"}
                  </button>
                </form>
              </div>
            )
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

"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../hooks/useAuth";
import { doctores, pacientes, citas } from "../../services/api";
import Combobox from "../../components/Combobox";

export default function NuevaCitaPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth(["admin", "administrativo"]);
  const [doctoresList, setDoctoresList] = useState([]);
  const [pacientesList, setPacientesList] = useState([]);
  const [especialidad, setEspecialidad] = useState("");
  const [slots, setSlots] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [cargandoSlots, setCargandoSlots] = useState(false);
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);

  const [form, setForm] = useState({
    paciente_id: "",
    doctor_id: "",
    fecha: "",
    hora: "",
    motivo: "",
  });

  useEffect(() => {
    if (!user) return;
    async function init() {
      try {
        const [docs, pacs] = await Promise.all([doctores.listar(), pacientes.listar()]);
        setDoctoresList(docs);
        setPacientesList(pacs);
      } catch (err) {
        setError(err.message);
      } finally {
        setDataLoading(false);
      }
    }
    init();
  }, [user]);

  useEffect(() => {
    async function cargarSlots() {
      if (!form.doctor_id || !form.fecha) { setSlots([]); return; }
      setCargandoSlots(true);
      try {
        const data = await citas.disponibles(form.doctor_id, form.fecha);
        setSlots(data.slots || []);
      } catch {
        setSlots([]);
      } finally {
        setCargandoSlots(false);
      }
    }
    cargarSlots();
  }, [form.doctor_id, form.fecha]);

  function handleChange(e) {
    const { name, value } = e.target;
    if (name === "doctor_id" || name === "fecha") {
      setForm((f) => ({ ...f, [name]: value, hora: "" }));
    } else {
      setForm((f) => ({ ...f, [name]: value }));
    }
  }

  function handleEspecialidadChange(e) {
    setEspecialidad(e.target.value);
    setForm((f) => ({ ...f, doctor_id: "", hora: "" }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setEnviando(true);
    setError("");
    try {
      await citas.crear({
        paciente_id: parseInt(form.paciente_id),
        doctor_id: parseInt(form.doctor_id),
        fecha: form.fecha,
        hora: form.hora,
        motivo: form.motivo,
      });
      router.push("/citas");
    } catch (err) {
      setError(err.message);
    } finally {
      setEnviando(false);
    }
  }

  const hoy = new Date().toISOString().split("T")[0];

  const especialidades = [...new Set(doctoresList.map((d) => d.especialidad))].sort();

  const doctoresFiltrados = especialidad
    ? doctoresList.filter((d) => d.especialidad === especialidad && d.activo !== false)
    : doctoresList.filter((d) => d.activo !== false);

  const doctoresOptions = doctoresFiltrados.map((d) => ({
    id: d.id,
    label: `Dr. ${d.nombre} ${d.apellido} — ${d.especialidad}`,
  }));

  const pacientesOptions = pacientesList.map((p) => ({
    id: p.id,
    label: `${p.nombre} ${p.apellido} — ${p.documento}`,
    searchText: p.documento,
  }));

  const comboClass =
    "w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent pr-8";

  const canSubmit = form.paciente_id && form.doctor_id && form.hora && !enviando;

  if (authLoading) return <div className="text-center py-12 text-gray-400">Cargando...</div>;
  if (dataLoading) return <div className="text-center py-12 text-gray-400">Cargando datos...</div>;

  return (
    <div className="max-w-xl mx-auto">
      <button
        onClick={() => router.back()}
        className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-6 transition-colors"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
        </svg>
        Volver
      </button>

      <div className="bg-white rounded-2xl border border-gray-100 p-6">
        <h1 className="text-xl font-extrabold text-gray-900 mb-1">Nueva Cita</h1>
        <p className="text-sm text-gray-500 mb-6">
          El horario se bloquea con locking distribuido en Redis para evitar doble reserva.
        </p>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Especialidad</label>
            <select
              value={especialidad}
              onChange={handleEspecialidadChange}
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
            >
              <option value="">Todas las especialidades</option>
              {especialidades.map((esp) => (
                <option key={esp} value={esp}>{esp}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Doctor</label>
            <Combobox
              options={doctoresOptions}
              value={form.doctor_id}
              onChange={(id) => setForm((f) => ({ ...f, doctor_id: id, hora: "" }))}
              placeholder="Buscar doctor..."
              inputClassName={comboClass}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Paciente</label>
            <Combobox
              options={pacientesOptions}
              value={form.paciente_id}
              onChange={(id) => setForm((f) => ({ ...f, paciente_id: id }))}
              placeholder="Buscar por nombre o número de documento..."
              inputClassName={comboClass}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Fecha</label>
            <input
              name="fecha"
              type="date"
              value={form.fecha}
              onChange={handleChange}
              min={hoy}
              required
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Hora</label>
            {cargandoSlots ? (
              <p className="text-sm text-gray-400 py-2">Cargando horarios disponibles...</p>
            ) : slots.length === 0 && form.doctor_id && form.fecha ? (
              <p className="text-sm text-amber-600 py-2">No hay horarios disponibles para esta fecha.</p>
            ) : (
              <div className="grid grid-cols-4 gap-2">
                {slots.map((slot) => (
                  <button
                    key={slot.hora}
                    type="button"
                    disabled={!slot.disponible}
                    onClick={() => setForm({ ...form, hora: slot.hora })}
                    className={`py-2 px-3 rounded-lg text-sm font-medium transition-all border ${
                      form.hora === slot.hora
                        ? "bg-brand-600 text-white border-brand-600"
                        : slot.disponible
                          ? "bg-white text-gray-700 border-gray-200 hover:border-brand-300 hover:bg-brand-50"
                          : "bg-gray-50 text-gray-300 border-gray-100 cursor-not-allowed line-through"
                    }`}
                  >
                    {slot.hora}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Motivo de la consulta</label>
            <textarea
              name="motivo"
              value={form.motivo}
              onChange={handleChange}
              required
              rows={3}
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent resize-none"
              placeholder="Describa el motivo de la consulta..."
            />
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">{error}</div>
          )}

          <button
            type="submit"
            disabled={!canSubmit}
            className="w-full py-3 bg-brand-600 text-white rounded-lg font-semibold hover:bg-brand-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {enviando ? "Reservando..." : "Reservar Cita"}
          </button>
        </form>
      </div>
    </div>
  );
}

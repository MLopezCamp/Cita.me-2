"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../../hooks/useAuth";
import { doctores, citas } from "../../../services/api";

export default function PortalNuevaCitaPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth("paciente");
  const [doctoresList, setDoctoresList] = useState([]);
  const [slots, setSlots] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [cargandoSlots, setCargandoSlots] = useState(false);
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);

  const [form, setForm] = useState({
    doctor_id: "",
    fecha: "",
    hora: "",
    motivo: "",
  });

  useEffect(() => {
    if (!user) return;
    async function init() {
      try {
        const data = await doctores.listar();
        setDoctoresList(data);
      } catch (err) { setError(err.message); }
      finally { setDataLoading(false); }
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
      } catch (err) { setSlots([]); }
      finally { setCargandoSlots(false); }
    }
    cargarSlots();
  }, [form.doctor_id, form.fecha]);

  function handleChange(e) {
    const value = e.target.value;
    setForm((f) => ({ ...f, [e.target.name]: value }));
    if (e.target.name === "doctor_id" || e.target.name === "fecha") {
      setForm((f) => ({ ...f, [e.target.name]: value, hora: "" }));
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setEnviando(true);
    setError("");
    try {
      await citas.crear({
        paciente_id: user.id,
        doctor_id: parseInt(form.doctor_id),
        fecha: form.fecha,
        hora: form.hora,
        motivo: form.motivo,
      });
      router.push("/portal");
    } catch (err) { setError(err.message); }
    finally { setEnviando(false); }
  }

  const hoy = new Date().toISOString().split("T")[0];

  if (authLoading) return <div className="text-center py-12 text-gray-400">Cargando...</div>;
  if (dataLoading) return <div className="text-center py-12 text-gray-400">Cargando...</div>;

  return (
    <div className="max-w-xl mx-auto">
      <button onClick={() => router.back()}
        className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-6 transition-colors">
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
        </svg>
        Volver a mi panel
      </button>

      <div className="bg-white rounded-2xl border border-gray-100 p-6">
        <h1 className="text-xl font-extrabold text-gray-900 mb-1">Pedir Cita</h1>
        <p className="text-sm text-gray-500 mb-6">
          Hola, {user?.nombre}. Seleccione doctor, fecha y horario.
        </p>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Doctor</label>
            <select name="doctor_id" value={form.doctor_id} onChange={handleChange} required
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent">
              <option value="">Seleccionar doctor...</option>
              {doctoresList.map((d) => (
                <option key={d.id} value={d.id}>Dr. {d.nombre} {d.apellido} — {d.especialidad}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Fecha</label>
            <input name="fecha" type="date" value={form.fecha} onChange={handleChange} min={hoy} required
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent" />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Horario disponible</label>
            {cargandoSlots ? (
              <p className="text-sm text-gray-400 py-2">Cargando horarios...</p>
            ) : slots.length === 0 && form.doctor_id && form.fecha ? (
              <p className="text-sm text-amber-600 py-2">No hay horarios disponibles para esa fecha.</p>
            ) : (
              <div className="grid grid-cols-4 gap-2">
                {slots.map((slot) => (
                  <button key={slot.hora} type="button" disabled={!slot.disponible}
                    onClick={() => setForm({ ...form, hora: slot.hora })}
                    className={`py-2 px-3 rounded-lg text-sm font-medium transition-all border ${
                      form.hora === slot.hora
                        ? "bg-sky-600 text-white border-sky-600"
                        : slot.disponible
                          ? "bg-white text-gray-700 border-gray-200 hover:border-sky-300 hover:bg-sky-50"
                          : "bg-gray-50 text-gray-300 border-gray-100 cursor-not-allowed line-through"
                    }`}>
                    {slot.hora}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Motivo de la consulta</label>
            <textarea name="motivo" value={form.motivo} onChange={handleChange} required rows={3}
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent resize-none"
              placeholder="Describa por qué necesita la cita..." />
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">{error}</div>
          )}

          <button type="submit" disabled={enviando || !form.hora}
            className="w-full py-3 bg-sky-600 text-white rounded-lg font-semibold hover:bg-sky-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
            {enviando ? "Reservando..." : "Confirmar Reserva"}
          </button>
        </form>
      </div>
    </div>
  );
}
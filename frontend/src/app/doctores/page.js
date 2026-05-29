"use client";
import { useEffect, useState } from "react";
import { useAuth } from "../../hooks/useAuth";
import { doctores, horarios } from "../../services/api";
import Modal from "../../components/Modal";

const ESPECIALIDADES = [
  "Medicina General", "Cardiología", "Dermatología", "Neurología",
  "Pediatría", "Traumatología", "Ginecología", "Oftalmología",
];

export default function DoctoresPage() {
  const { user, loading: authLoading } = useAuth(["admin", "administrativo"]);
  const [lista, setLista] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [modalDoctor, setModalDoctor] = useState(false);
  const [modalHorario, setModalHorario] = useState(false);
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [horariosDoc, setHorariosDoc] = useState([]);
  const [doctorSeleccionado, setDoctorSeleccionado] = useState(null);

  const [formDoctor, setFormDoctor] = useState({
    nombre: "", apellido: "", especialidad: "", email: "", telefono: "",
  });

  const [formHorario, setFormHorario] = useState({
    doctor_id: "", dia_semana: "0", hora_inicio: "08:00", hora_fin: "12:00",
  });

  const DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];

  useEffect(() => {
    if (!user) return;
    cargarDoctores();
  }, [user]);

  async function cargarDoctores() {
    try {
      const data = await doctores.listar();
      setLista(data);
    } catch (err) { setError(err.message); }
    finally { setDataLoading(false); }
  }

  async function handleCrearDoctor(e) {
    e.preventDefault();
    setEnviando(true);
    setError("");
    try {
      await doctores.crear(formDoctor);
      setModalDoctor(false);
      setFormDoctor({ nombre: "", apellido: "", especialidad: "", email: "", telefono: "" });
      await cargarDoctores();
    } catch (err) { setError(err.message); }
    finally { setEnviando(false); }
  }

  async function verHorarios(doctor) {
    setDoctorSeleccionado(doctor);
    setFormHorario((f) => ({ ...f, doctor_id: doctor.id }));
    try {
      const data = await horarios.porDoctor(doctor.id);
      setHorariosDoc(data);
    } catch (err) { setError(err.message); }
    setModalHorario(true);
  }

  async function handleCrearHorario(e) {
    e.preventDefault();
    setEnviando(true);
    setError("");
    try {
      await horarios.crear({
        doctor_id: parseInt(formHorario.doctor_id),
        dia_semana: parseInt(formHorario.dia_semana),
        hora_inicio: formHorario.hora_inicio,
        hora_fin: formHorario.hora_fin,
      });
      const data = await horarios.porDoctor(parseInt(formHorario.doctor_id));
      setHorariosDoc(data);
    } catch (err) { setError(err.message); }
    finally { setEnviando(false); }
  }

  if (authLoading) return <div className="text-center py-12 text-gray-400">Cargando...</div>;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-extrabold text-gray-900">Doctores</h1>
          <p className="text-sm text-gray-500">{lista.length} registrados</p>
        </div>
        <button onClick={() => setModalDoctor(true)}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-brand-600 text-white rounded-lg font-medium hover:bg-brand-700 transition-colors">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          Nuevo Doctor
        </button>
      </div>

      {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">{error}</div>}

      {dataLoading ? (
        <div className="text-center py-12 text-gray-400">Cargando...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {lista.map((d, i) => (
            <div key={d.id} className="card-animate bg-white rounded-xl border border-gray-100 p-5 hover:shadow-md transition-all" style={{ animationDelay: `${i * 60}ms` }}>
              <div className="flex items-start justify-between mb-3">
                <div className="w-10 h-10 rounded-xl bg-amber-100 flex items-center justify-center text-amber-700 font-bold text-sm">
                  {d.nombre[0]}{d.apellido[0]}
                </div>
                <span className="text-xs font-medium text-brand-600 bg-brand-50 px-2 py-1 rounded-md">{d.especialidad}</span>
              </div>
              <h3 className="font-bold text-gray-800">Dr. {d.nombre} {d.apellido}</h3>
              <p className="text-sm text-gray-500 mt-1">{d.email}</p>
              <p className="text-sm text-gray-500">{d.telefono}</p>
              <button onClick={() => verHorarios(d)}
                className="mt-4 w-full py-2 text-sm font-medium text-brand-600 bg-brand-50 rounded-lg hover:bg-brand-100 transition-colors">
                Ver Horarios
              </button>
            </div>
          ))}
          {lista.length === 0 && (
            <div className="col-span-full text-center py-16 bg-white rounded-xl border border-gray-100">
              <p className="text-gray-400">No hay doctores registrados</p>
            </div>
          )}
        </div>
      )}

      {/* Modal crear doctor */}
      <Modal isOpen={modalDoctor} onClose={() => setModalDoctor(false)} title="Nuevo Doctor">
        <form onSubmit={handleCrearDoctor} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nombre</label>
              <input name="nombre" value={formDoctor.nombre} onChange={(e) => setFormDoctor({...formDoctor, nombre: e.target.value})} required
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Apellido</label>
              <input name="apellido" value={formDoctor.apellido} onChange={(e) => setFormDoctor({...formDoctor, apellido: e.target.value})} required
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Especialidad</label>
            <select value={formDoctor.especialidad} onChange={(e) => setFormDoctor({...formDoctor, especialidad: e.target.value})} required
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent">
              <option value="">Seleccionar...</option>
              {ESPECIALIDADES.map((e) => <option key={e} value={e}>{e}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input name="email" type="email" value={formDoctor.email} onChange={(e) => setFormDoctor({...formDoctor, email: e.target.value})} required
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Teléfono</label>
            <input name="telefono" value={formDoctor.telefono} onChange={(e) => setFormDoctor({...formDoctor, telefono: e.target.value})} required
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent" />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button type="submit" disabled={enviando} className="w-full py-2.5 bg-brand-600 text-white rounded-lg font-medium hover:bg-brand-700 transition-colors disabled:opacity-50">
            {enviando ? "Guardando..." : "Registrar Doctor"}
          </button>
        </form>
      </Modal>

      {/* Modal horarios */}
      <Modal isOpen={modalHorario} onClose={() => setModalHorario(false)} title={`Horarios — Dr. ${doctorSeleccionado?.nombre} ${doctorSeleccionado?.apellido}`}>
        <div className="space-y-4">
          {horariosDoc.length > 0 && (
            <div className="space-y-2">
              {horariosDoc.map((h) => (
                <div key={h.id} className="flex items-center justify-between px-3 py-2 bg-gray-50 rounded-lg text-sm">
                  <span className="font-medium text-gray-700">{DIAS[h.dia_semana]}</span>
                  <span className="text-gray-500">{h.hora_inicio} — {h.hora_fin}</span>
                </div>
              ))}
            </div>
          )}
          {horariosDoc.length === 0 && <p className="text-sm text-gray-400 text-center py-4">Sin horarios asignados</p>}

          <hr className="border-gray-100" />

          <form onSubmit={handleCrearHorario} className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Día</label>
              <select value={formHorario.dia_semana} onChange={(e) => setFormHorario({...formHorario, dia_semana: e.target.value})}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent">
                {DIAS.map((d, i) => <option key={i} value={i}>{d}</option>)}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Desde</label>
                <input type="time" value={formHorario.hora_inicio} onChange={(e) => setFormHorario({...formHorario, hora_inicio: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Hasta</label>
                <input type="time" value={formHorario.hora_fin} onChange={(e) => setFormHorario({...formHorario, hora_fin: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent" />
              </div>
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <button type="submit" disabled={enviando} className="w-full py-2 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700 transition-colors disabled:opacity-50">
              Agregar Horario
            </button>
          </form>
        </div>
      </Modal>
    </div>
  );
}
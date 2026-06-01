"use client";
import { useEffect, useState } from "react";
import { useAuth } from "../../hooks/useAuth";
import { doctores, horarios } from "../../services/api";
import Modal from "../../components/Modal";

const ESPECIALIDADES = [
  "Medicina General", "Cardiología", "Dermatología", "Neurología",
  "Pediatría", "Traumatología", "Ginecología", "Oftalmología",
];

function generarContrasena() {
  const chars = "ABCDEFGHJKMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789";
  return Array.from({ length: 10 }, () => chars[Math.floor(Math.random() * chars.length)]).join("");
}

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
  const [confirmandoId, setConfirmandoId] = useState(null);
  const [mostrarContrasena, setMostrarContrasena] = useState(false);

  const [formDoctor, setFormDoctor] = useState({
    nombre: "", apellido: "", especialidad: "", email: "", telefono: "", contrasena: "",
  });

  const [formHorario, setFormHorario] = useState({
    doctor_id: "", fechas: [""], hora_inicio: "08:00", hora_fin: "12:00",
  });
  const [editandoHorario, setEditandoHorario] = useState(null);
  const [formEdit, setFormEdit] = useState({ fecha: "", hora_inicio: "", hora_fin: "" });
  const [confirmandoHorarioId, setConfirmandoHorarioId] = useState(null);

  useEffect(() => {
    if (!user) return;
    cargarDoctores();
  }, [user]);

  async function cargarDoctores() {
    try {
      const data = await doctores.listar();
      setLista(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setDataLoading(false);
    }
  }

  function abrirModalDoctor() {
    setFormDoctor({ nombre: "", apellido: "", especialidad: "", email: "", telefono: "", contrasena: "" });
    setError("");
    setMostrarContrasena(false);
    setModalDoctor(true);
  }

  async function handleCrearDoctor(e) {
    e.preventDefault();
    setEnviando(true);
    setError("");
    try {
      await doctores.crear(formDoctor);
      setModalDoctor(false);
      await cargarDoctores();
    } catch (err) {
      setError(err.message);
    } finally {
      setEnviando(false);
    }
  }

  async function handleToggleActivo(id) {
    setError("");
    try {
      await doctores.toggleActivo(id);
      await cargarDoctores();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleEliminar(id) {
    setError("");
    try {
      await doctores.eliminar(id);
      setConfirmandoId(null);
      await cargarDoctores();
    } catch (err) {
      setError(err.message);
      setConfirmandoId(null);
    }
  }

  async function verHorarios(doctor) {
    setDoctorSeleccionado(doctor);
    setFormHorario({ doctor_id: doctor.id, fechas: [""], hora_inicio: "08:00", hora_fin: "12:00" });
    setEditandoHorario(null);
    setError("");
    try {
      const data = await horarios.porDoctor(doctor.id);
      setHorariosDoc(data);
    } catch (err) {
      setError(err.message);
    }
    setModalHorario(true);
  }

  async function handleCrearHorarios(e) {
    e.preventDefault();
    setEnviando(true);
    setError("");
    const fechasValidas = formHorario.fechas.filter((f) => f.trim() !== "");
    if (fechasValidas.length === 0) {
      setError("Debe ingresar al menos una fecha.");
      setEnviando(false);
      return;
    }
    try {
      await horarios.crearLote({
        doctor_id: parseInt(formHorario.doctor_id),
        fechas: fechasValidas,
        hora_inicio: formHorario.hora_inicio,
        hora_fin: formHorario.hora_fin,
      });
      setFormHorario((f) => ({ ...f, fechas: [""] }));
      const data = await horarios.porDoctor(parseInt(formHorario.doctor_id));
      setHorariosDoc(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setEnviando(false);
    }
  }

  function abrirEdicion(h) {
    setEditandoHorario(h);
    setFormEdit({ fecha: h.fecha, hora_inicio: h.hora_inicio.slice(0, 5), hora_fin: h.hora_fin.slice(0, 5) });
    setError("");
  }

  async function handleGuardarEdicion(e) {
    e.preventDefault();
    setEnviando(true);
    setError("");
    try {
      await horarios.actualizar(editandoHorario.id, {
        doctor_id: doctorSeleccionado.id,
        fecha: formEdit.fecha,
        hora_inicio: formEdit.hora_inicio,
        hora_fin: formEdit.hora_fin,
      });
      setEditandoHorario(null);
      const data = await horarios.porDoctor(doctorSeleccionado.id);
      setHorariosDoc(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setEnviando(false);
    }
  }

  async function handleEliminarHorario(id) {
    setError("");
    try {
      await horarios.desactivar(id);
      setConfirmandoHorarioId(null);
      const data = await horarios.porDoctor(doctorSeleccionado.id);
      setHorariosDoc(data);
    } catch (err) {
      setError(err.message);
      setConfirmandoHorarioId(null);
    }
  }

  const inputClass = "w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent";

  if (authLoading) return <div className="text-center py-12 text-gray-400">Cargando...</div>;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-extrabold text-gray-900">Doctores</h1>
          <p className="text-sm text-gray-500">{lista.length} registrados</p>
        </div>
        <button onClick={abrirModalDoctor}
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
            <div key={d.id} className={`card-animate bg-white rounded-xl border p-5 hover:shadow-md transition-all ${d.activo ? "border-gray-100" : "border-gray-200 opacity-60"}`} style={{ animationDelay: `${i * 60}ms` }}>
              <div className="flex items-start justify-between mb-3">
                <div className="w-10 h-10 rounded-xl bg-amber-100 flex items-center justify-center text-amber-700 font-bold text-sm">
                  {d.nombre[0]}{d.apellido[0]}
                </div>
                <div className="flex items-center gap-2">
                  {!d.activo && <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-md">Inactivo</span>}
                  <span className="text-xs font-medium text-brand-600 bg-brand-50 px-2 py-1 rounded-md">{d.especialidad}</span>
                </div>
              </div>
              <h3 className="font-bold text-gray-800">Dr. {d.nombre} {d.apellido}</h3>
              <p className="text-sm text-gray-500 mt-1">{d.email}</p>
              <p className="text-sm text-gray-500">{d.telefono}</p>
              <div className="mt-4 flex gap-2">
                <button onClick={() => verHorarios(d)}
                  className="flex-1 py-2 text-sm font-medium text-brand-600 bg-brand-50 rounded-lg hover:bg-brand-100 transition-colors">
                  Horarios
                </button>
                {user?.rol === "admin" && (
                  <>
                    <button
                      onClick={() => handleToggleActivo(d.id)}
                      title={d.activo ? "Desactivar doctor" : "Activar doctor"}
                      className={`px-3 py-2 text-sm rounded-lg transition-colors ${
                        d.activo
                          ? "text-amber-500 hover:text-amber-700 hover:bg-amber-50"
                          : "text-emerald-500 hover:text-emerald-700 hover:bg-emerald-50"
                      }`}
                    >
                      {d.activo ? (
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                        </svg>
                      ) : (
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      )}
                    </button>
                    {confirmandoId === d.id ? (
                      <div className="flex items-center gap-1 px-1">
                        <span className="text-xs text-gray-500">¿Eliminar?</span>
                        <button onClick={() => handleEliminar(d.id)} className="text-xs text-red-600 font-semibold hover:underline">Sí</button>
                        <button onClick={() => setConfirmandoId(null)} className="text-xs text-gray-400 hover:underline">No</button>
                      </div>
                    ) : (
                      <button
                        onClick={() => setConfirmandoId(d.id)}
                        className="px-3 py-2 text-sm text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        title="Eliminar doctor"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                        </svg>
                      </button>
                    )}
                  </>
                )}
              </div>
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
              <input name="nombre" value={formDoctor.nombre} onChange={(e) => setFormDoctor({ ...formDoctor, nombre: e.target.value })} required className={inputClass} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Apellido</label>
              <input name="apellido" value={formDoctor.apellido} onChange={(e) => setFormDoctor({ ...formDoctor, apellido: e.target.value })} required className={inputClass} />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Especialidad</label>
            <select value={formDoctor.especialidad} onChange={(e) => setFormDoctor({ ...formDoctor, especialidad: e.target.value })} required className={inputClass}>
              <option value="">Seleccionar...</option>
              {ESPECIALIDADES.map((e) => <option key={e} value={e}>{e}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input name="email" type="email" value={formDoctor.email} onChange={(e) => setFormDoctor({ ...formDoctor, email: e.target.value })} required className={inputClass} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Teléfono</label>
            <input name="telefono" value={formDoctor.telefono} onChange={(e) => setFormDoctor({ ...formDoctor, telefono: e.target.value })} required className={inputClass} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Contraseña</label>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <input
                  type={mostrarContrasena ? "text" : "password"}
                  value={formDoctor.contrasena}
                  onChange={(e) => setFormDoctor({ ...formDoctor, contrasena: e.target.value })}
                  required
                  minLength={4}
                  placeholder="Mínimo 4 caracteres"
                  className={inputClass + " pr-9"}
                />
                <button
                  type="button"
                  onClick={() => setMostrarContrasena((v) => !v)}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  tabIndex={-1}
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    {mostrarContrasena
                      ? <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
                      : <><path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" /><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></>
                    }
                  </svg>
                </button>
              </div>
              <button
                type="button"
                onClick={() => { setFormDoctor((f) => ({ ...f, contrasena: generarContrasena() })); setMostrarContrasena(true); }}
                className="px-3 py-2 text-xs font-medium text-brand-600 bg-brand-50 rounded-lg hover:bg-brand-100 transition-colors whitespace-nowrap"
              >
                Generar
              </button>
            </div>
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button type="submit" disabled={enviando} className="w-full py-2.5 bg-brand-600 text-white rounded-lg font-medium hover:bg-brand-700 transition-colors disabled:opacity-50">
            {enviando ? "Guardando..." : "Registrar Doctor"}
          </button>
        </form>
      </Modal>

      {/* Modal horarios */}
      <Modal isOpen={modalHorario} onClose={() => { setModalHorario(false); setEditandoHorario(null); setError(""); }} title={`Horarios — Dr. ${doctorSeleccionado?.nombre} ${doctorSeleccionado?.apellido}`}>
        <div className="space-y-4">

          {/* Lista de horarios existentes */}
          {horariosDoc.length > 0 ? (
            <div className="space-y-1">
              {horariosDoc.map((h) => (
                <div key={h.id} className="rounded-lg overflow-hidden">
                  {/* Fila principal */}
                  <div className={`flex items-center gap-2 px-3 py-2 text-sm group ${editandoHorario?.id === h.id ? "bg-brand-50 border border-brand-200 rounded-t-lg border-b-0" : "bg-gray-50"}`}>
                    <span className="font-medium text-gray-700 tabular-nums w-28 shrink-0">
                      {h.hora_inicio.slice(0, 5)} — {h.hora_fin.slice(0, 5)}
                    </span>
                    <span className="text-gray-400 text-xs flex-1">{h.fecha}</span>
                    {editandoHorario?.id !== h.id && (
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                        <button onClick={() => { setConfirmandoHorarioId(null); abrirEdicion(h); }} title="Editar"
                          className="p-1 text-gray-400 hover:text-brand-600 transition-colors">
                          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125" />
                          </svg>
                        </button>
                        {confirmandoHorarioId === h.id ? (
                          <span className="flex items-center gap-1 text-xs">
                            <span className="text-gray-400">¿Eliminar?</span>
                            <button onClick={() => handleEliminarHorario(h.id)} className="text-red-500 font-semibold hover:underline">Si</button>
                            <button onClick={() => setConfirmandoHorarioId(null)} className="text-gray-400 hover:underline">No</button>
                          </span>
                        ) : (
                          <button onClick={() => { setEditandoHorario(null); setConfirmandoHorarioId(h.id); }} title="Eliminar"
                            className="p-1 text-gray-400 hover:text-red-500 transition-colors">
                            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                            </svg>
                          </button>
                        )}
                      </div>
                    )}
                    {editandoHorario?.id === h.id && (
                      <button type="button" onClick={() => { setEditandoHorario(null); setError(""); }}
                        className="text-xs text-gray-400 hover:text-gray-600 shrink-0 ml-auto">
                        Cancelar
                      </button>
                    )}
                  </div>

                  {/* Panel de edicion expandible */}
                  {editandoHorario?.id === h.id && (
                    <form onSubmit={handleGuardarEdicion}
                      className="px-3 py-3 bg-brand-50 border border-brand-200 border-t-0 rounded-b-lg space-y-2">
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">Fecha</label>
                        <input type="date" value={formEdit.fecha}
                          onChange={(e) => setFormEdit({ ...formEdit, fecha: e.target.value })}
                          required className="w-full px-2 py-1.5 border border-gray-200 rounded text-sm focus:outline-none focus:ring-1 focus:ring-brand-500 bg-white" />
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">Desde</label>
                          <input type="time" value={formEdit.hora_inicio}
                            onChange={(e) => setFormEdit({ ...formEdit, hora_inicio: e.target.value })}
                            required className="w-full px-2 py-1.5 border border-gray-200 rounded text-sm focus:outline-none focus:ring-1 focus:ring-brand-500 bg-white" />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">Hasta</label>
                          <input type="time" value={formEdit.hora_fin}
                            onChange={(e) => setFormEdit({ ...formEdit, hora_fin: e.target.value })}
                            required className="w-full px-2 py-1.5 border border-gray-200 rounded text-sm focus:outline-none focus:ring-1 focus:ring-brand-500 bg-white" />
                        </div>
                      </div>
                      <button type="submit" disabled={enviando}
                        className="w-full py-1.5 bg-brand-600 text-white rounded text-xs font-medium hover:bg-brand-700 transition-colors disabled:opacity-50">
                        {enviando ? "Guardando..." : "Guardar cambios"}
                      </button>
                    </form>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-400 text-center py-4">Sin horarios asignados</p>
          )}

          {error && <p className="text-sm text-red-600">{error}</p>}

          <hr className="border-gray-100" />

          {/* Formulario creacion multifecha */}
          <form onSubmit={handleCrearHorarios} className="space-y-3">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Agregar fechas</p>

            <div className="space-y-2">
              {formHorario.fechas.map((fecha, idx) => (
                <div key={idx} className="flex items-center gap-2">
                  <input
                    type="date"
                    value={fecha}
                    onChange={(e) => {
                      const nuevas = [...formHorario.fechas];
                      nuevas[idx] = e.target.value;
                      setFormHorario({ ...formHorario, fechas: nuevas });
                    }}
                    required
                    min={new Date().toISOString().split("T")[0]}
                    className={inputClass + " flex-1"}
                  />
                  {formHorario.fechas.length > 1 && (
                    <button
                      type="button"
                      onClick={() => setFormHorario({ ...formHorario, fechas: formHorario.fechas.filter((_, i) => i !== idx) })}
                      className="p-1.5 text-gray-300 hover:text-red-400 transition-colors"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  )}
                </div>
              ))}
            </div>

            <button
              type="button"
              onClick={() => setFormHorario({ ...formHorario, fechas: [...formHorario.fechas, ""] })}
              className="flex items-center gap-1.5 text-sm text-brand-600 hover:text-brand-700 font-medium"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
              </svg>
              Agregar otra fecha
            </button>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Desde</label>
                <input type="time" value={formHorario.hora_inicio} onChange={(e) => setFormHorario({ ...formHorario, hora_inicio: e.target.value })}
                  className={inputClass} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Hasta</label>
                <input type="time" value={formHorario.hora_fin} onChange={(e) => setFormHorario({ ...formHorario, hora_fin: e.target.value })}
                  className={inputClass} />
              </div>
            </div>

            <button type="submit" disabled={enviando} className="w-full py-2 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700 transition-colors disabled:opacity-50">
              {enviando ? "Guardando..." : `Agregar ${formHorario.fechas.filter(f => f).length > 1 ? `${formHorario.fechas.filter(f => f).length} fechas` : "horario"}`}
            </button>
          </form>
        </div>
      </Modal>
    </div>
  );
}

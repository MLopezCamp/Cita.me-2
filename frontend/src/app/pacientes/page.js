"use client";
import { useEffect, useState } from "react";
import { useAuth } from "../../hooks/useAuth";
import { pacientes } from "../../services/api";
import Modal from "../../components/Modal";

function generarContrasena() {
  const chars = "ABCDEFGHJKMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789";
  return Array.from({ length: 10 }, () => chars[Math.floor(Math.random() * chars.length)]).join("");
}

const FORM_VACIO = {
  nombre: "", apellido: "", documento: "", email: "", telefono: "",
  fecha_nacimiento: "", contrasena: "",
};

export default function PacientesPage() {
  const { user, loading: authLoading } = useAuth(["admin", "administrativo"]);
  const [lista, setLista] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editandoId, setEditandoId] = useState(null);
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [confirmandoId, setConfirmandoId] = useState(null);
  const [mostrarContrasena, setMostrarContrasena] = useState(false);

  const [form, setForm] = useState(FORM_VACIO);

  useEffect(() => {
    if (!user) return;
    cargarPacientes();
  }, [user]);

  async function cargarPacientes() {
    try {
      const data = await pacientes.listar();
      setLista(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setDataLoading(false);
    }
  }

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  function abrirModalNuevo() {
    setEditandoId(null);
    setForm(FORM_VACIO);
    setError("");
    setMostrarContrasena(false);
    setModalOpen(true);
  }

  function abrirModalEditar(p) {
    setEditandoId(p.id);
    setForm({
      nombre: p.nombre,
      apellido: p.apellido,
      documento: p.documento,
      email: p.email,
      telefono: p.telefono,
      fecha_nacimiento: p.fecha_nacimiento,
      contrasena: "",
    });
    setError("");
    setMostrarContrasena(false);
    setModalOpen(true);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setEnviando(true);
    setError("");
    try {
      if (editandoId) {
        await pacientes.actualizar(editandoId, form);
      } else {
        await pacientes.crear(form);
      }
      setModalOpen(false);
      await cargarPacientes();
    } catch (err) {
      setError(err.message);
    } finally {
      setEnviando(false);
    }
  }

  async function handleEliminar(id) {
    setError("");
    try {
      await pacientes.eliminar(id);
      setConfirmandoId(null);
      await cargarPacientes();
    } catch (err) {
      setError(err.message);
      setConfirmandoId(null);
    }
  }

  const inputClass = "w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent";

  if (authLoading) return <div className="text-center py-12 text-gray-400">Cargando...</div>;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-extrabold text-gray-900">Pacientes</h1>
          <p className="text-sm text-gray-500">{lista.length} registrados</p>
        </div>
        <button
          onClick={abrirModalNuevo}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-brand-600 text-white rounded-lg font-medium hover:bg-brand-700 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          Nuevo Paciente
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">{error}</div>
      )}

      {dataLoading ? (
        <div className="text-center py-12 text-gray-400">Cargando...</div>
      ) : lista.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-xl border border-gray-100">
          <p className="text-gray-400 text-lg mb-2">No hay pacientes registrados</p>
          <p className="text-gray-300 text-sm">Haga clic en "Nuevo Paciente" para comenzar</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="text-left px-5 py-3 font-semibold text-gray-500">Nombre</th>
                <th className="text-left px-5 py-3 font-semibold text-gray-500">Documento</th>
                <th className="text-left px-5 py-3 font-semibold text-gray-500">Email</th>
                <th className="text-left px-5 py-3 font-semibold text-gray-500">Teléfono</th>
                <th className="text-left px-5 py-3 font-semibold text-gray-500">Nacimiento</th>
                <th className="text-left px-5 py-3 font-semibold text-gray-500"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {lista.map((p, i) => (
                <tr key={p.id} className="card-animate hover:bg-gray-50 transition-colors" style={{ animationDelay: `${i * 40}ms` }}>
                  <td className="px-5 py-3 font-medium text-gray-800">{p.nombre} {p.apellido}</td>
                  <td className="px-5 py-3 text-gray-600 font-mono text-xs">{p.documento}</td>
                  <td className="px-5 py-3 text-gray-600">{p.email}</td>
                  <td className="px-5 py-3 text-gray-600">{p.telefono}</td>
                  <td className="px-5 py-3 text-gray-500">{p.fecha_nacimiento}</td>
                  <td className="px-5 py-3 text-right">
                    <span className="inline-flex items-center gap-3">
                      <button
                        onClick={() => abrirModalEditar(p)}
                        className="text-xs text-brand-600 hover:text-brand-800 transition-colors font-medium"
                      >
                        Editar
                      </button>
                      {user?.rol === "admin" && (
                        confirmandoId === p.id ? (
                          <span className="inline-flex items-center gap-2">
                            <span className="text-xs text-gray-500">¿Eliminar?</span>
                            <button onClick={() => handleEliminar(p.id)} className="text-xs text-red-600 font-semibold hover:underline">Sí</button>
                            <button onClick={() => setConfirmandoId(null)} className="text-xs text-gray-400 hover:underline">No</button>
                          </span>
                        ) : (
                          <button
                            onClick={() => setConfirmandoId(p.id)}
                            className="text-xs text-red-400 hover:text-red-600 transition-colors"
                          >
                            Eliminar
                          </button>
                        )
                      )}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} title={editandoId ? "Editar Paciente" : "Nuevo Paciente"}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nombre</label>
              <input name="nombre" value={form.nombre} onChange={handleChange} required className={inputClass} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Apellido</label>
              <input name="apellido" value={form.apellido} onChange={handleChange} required className={inputClass} />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Documento</label>
            <input name="documento" value={form.documento} onChange={handleChange} required className={inputClass} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input name="email" type="email" value={form.email} onChange={handleChange} required className={inputClass} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Teléfono</label>
              <input name="telefono" value={form.telefono} onChange={handleChange} required className={inputClass} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Fecha de nacimiento</label>
              <input name="fecha_nacimiento" type="date" value={form.fecha_nacimiento} onChange={handleChange} required className={inputClass} />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Contraseña {editandoId && <span className="font-normal text-gray-400">(dejar vacío para no cambiar)</span>}
            </label>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <input
                  name="contrasena"
                  type={mostrarContrasena ? "text" : "password"}
                  value={form.contrasena}
                  onChange={handleChange}
                  required={!editandoId}
                  minLength={editandoId ? 0 : 4}
                  placeholder={editandoId ? "Sin cambios" : "Mínimo 4 caracteres"}
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
                onClick={() => { setForm((f) => ({ ...f, contrasena: generarContrasena() })); setMostrarContrasena(true); }}
                className="px-3 py-2 text-xs font-medium text-brand-600 bg-brand-50 rounded-lg hover:bg-brand-100 transition-colors whitespace-nowrap"
              >
                Generar
              </button>
            </div>
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button type="submit" disabled={enviando}
            className="w-full py-2.5 bg-brand-600 text-white rounded-lg font-medium hover:bg-brand-700 transition-colors disabled:opacity-50">
            {enviando ? "Guardando..." : editandoId ? "Guardar Cambios" : "Registrar Paciente"}
          </button>
        </form>
      </Modal>
    </div>
  );
}

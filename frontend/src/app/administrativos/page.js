"use client";
import { useEffect, useState } from "react";
import { useAuth } from "../../hooks/useAuth";
import { administrativos } from "../../services/api";
import Modal from "../../components/Modal";

function generarContrasena() {
  const chars = "ABCDEFGHJKMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789";
  return Array.from({ length: 10 }, () => chars[Math.floor(Math.random() * chars.length)]).join("");
}

const FORM_VACIO = { nombre: "", apellido: "", email: "", telefono: "", contrasena: "" };

export default function AdministrativosPage() {
  const { user, loading: authLoading } = useAuth("admin");
  const [lista, setLista] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [error, setError] = useState("");

  // Modal crear
  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState(FORM_VACIO);
  const [enviando, setEnviando] = useState(false);
  const [mostrarContrasena, setMostrarContrasena] = useState(false);

  // Modal editar
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editId, setEditId] = useState(null);
  const [editForm, setEditForm] = useState(FORM_VACIO);
  const [editEnviando, setEditEnviando] = useState(false);
  const [editMostrarContrasena, setEditMostrarContrasena] = useState(false);

  // Confirmacion desactivar
  const [confirmandoId, setConfirmandoId] = useState(null);

  useEffect(() => {
    if (!user) return;
    cargarLista();
  }, [user]);

  async function cargarLista() {
    try {
      const data = await administrativos.listar();
      setLista(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setDataLoading(false);
    }
  }

  function abrirModal() {
    setForm(FORM_VACIO);
    setError("");
    setMostrarContrasena(false);
    setModalOpen(true);
  }

  function abrirEditar(a) {
    setEditId(a.id);
    setEditForm({ nombre: a.nombre, apellido: a.apellido, email: a.email, telefono: a.telefono, contrasena: "" });
    setError("");
    setEditMostrarContrasena(false);
    setEditModalOpen(true);
  }

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  function handleEditChange(e) {
    setEditForm({ ...editForm, [e.target.name]: e.target.value });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setEnviando(true);
    setError("");
    try {
      await administrativos.crear(form);
      setModalOpen(false);
      await cargarLista();
    } catch (err) {
      setError(err.message);
    } finally {
      setEnviando(false);
    }
  }

  async function handleEditar(e) {
    e.preventDefault();
    setEditEnviando(true);
    setError("");
    try {
      const payload = { ...editForm };
      if (!payload.contrasena) delete payload.contrasena;
      await administrativos.actualizar(editId, payload);
      setEditModalOpen(false);
      await cargarLista();
    } catch (err) {
      setError(err.message);
    } finally {
      setEditEnviando(false);
    }
  }

  async function handleEliminar(id) {
    setError("");
    try {
      await administrativos.eliminar(id);
      setConfirmandoId(null);
      await cargarLista();
    } catch (err) {
      setError(err.message);
      setConfirmandoId(null);
    }
  }

  async function handleActivar(id) {
    setError("");
    try {
      await administrativos.activar(id);
      await cargarLista();
    } catch (err) {
      setError(err.message);
    }
  }

  const inputClass = "w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent";

  if (authLoading) return <div className="text-center py-12 text-gray-400">Cargando...</div>;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-extrabold text-gray-900">Personal Administrativo</h1>
          <p className="text-sm text-gray-500">{lista.length} registrados</p>
        </div>
        <button
          onClick={abrirModal}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-brand-600 text-white rounded-lg font-medium hover:bg-brand-700 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          Nuevo Administrativo
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">{error}</div>
      )}

      {dataLoading ? (
        <div className="text-center py-12 text-gray-400">Cargando...</div>
      ) : lista.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-xl border border-gray-100">
          <p className="text-gray-400 text-lg mb-2">No hay personal administrativo registrado</p>
          <p className="text-gray-300 text-sm">Haga clic en "Nuevo Administrativo" para comenzar</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="text-left px-5 py-3 font-semibold text-gray-500">Nombre</th>
                <th className="text-left px-5 py-3 font-semibold text-gray-500">Email</th>
                <th className="text-left px-5 py-3 font-semibold text-gray-500">Telefono</th>
                <th className="text-left px-5 py-3 font-semibold text-gray-500">Estado</th>
                <th className="text-left px-5 py-3 font-semibold text-gray-500"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {lista.map((a, i) => (
                <tr key={a.id} className={`card-animate hover:bg-gray-50 transition-colors ${!a.activo ? "opacity-60" : ""}`} style={{ animationDelay: `${i * 40}ms` }}>
                  <td className="px-5 py-3 font-medium text-gray-800">{a.nombre} {a.apellido}</td>
                  <td className="px-5 py-3 text-gray-600">{a.email}</td>
                  <td className="px-5 py-3 text-gray-600">{a.telefono}</td>
                  <td className="px-5 py-3">
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${a.activo ? "bg-emerald-50 text-emerald-700" : "bg-gray-100 text-gray-500"}`}>
                      {a.activo ? "Activo" : "Inactivo"}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-right">
                    <span className="inline-flex items-center gap-3">
                      <button
                        onClick={() => abrirEditar(a)}
                        className="text-xs text-brand-600 hover:text-brand-800 transition-colors font-medium"
                      >
                        Editar
                      </button>
                      {a.activo ? (
                        confirmandoId === a.id ? (
                          <span className="inline-flex items-center gap-2">
                            <span className="text-xs text-gray-500">Desactivar?</span>
                            <button onClick={() => handleEliminar(a.id)} className="text-xs text-red-600 font-semibold hover:underline">Si</button>
                            <button onClick={() => setConfirmandoId(null)} className="text-xs text-gray-400 hover:underline">No</button>
                          </span>
                        ) : (
                          <button
                            onClick={() => setConfirmandoId(a.id)}
                            className="text-xs text-red-400 hover:text-red-600 transition-colors"
                          >
                            Desactivar
                          </button>
                        )
                      ) : (
                        <button
                          onClick={() => handleActivar(a.id)}
                          className="text-xs text-emerald-600 hover:text-emerald-800 transition-colors font-medium"
                        >
                          Activar
                        </button>
                      )}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal crear */}
      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} title="Nuevo Administrativo">
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
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input name="email" type="email" value={form.email} onChange={handleChange} required className={inputClass} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Telefono</label>
            <input name="telefono" value={form.telefono} onChange={handleChange} required className={inputClass} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Contrasena</label>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <input
                  name="contrasena"
                  type={mostrarContrasena ? "text" : "password"}
                  value={form.contrasena}
                  onChange={handleChange}
                  required
                  minLength={4}
                  placeholder="Minimo 4 caracteres"
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
            {enviando ? "Guardando..." : "Registrar Administrativo"}
          </button>
        </form>
      </Modal>

      {/* Modal editar */}
      <Modal isOpen={editModalOpen} onClose={() => setEditModalOpen(false)} title="Editar Administrativo">
        <form onSubmit={handleEditar} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nombre</label>
              <input name="nombre" value={editForm.nombre} onChange={handleEditChange} required className={inputClass} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Apellido</label>
              <input name="apellido" value={editForm.apellido} onChange={handleEditChange} required className={inputClass} />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input name="email" type="email" value={editForm.email} onChange={handleEditChange} required className={inputClass} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Telefono</label>
            <input name="telefono" value={editForm.telefono} onChange={handleEditChange} required className={inputClass} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nueva contrasena <span className="text-gray-400 font-normal">(dejar vacio para no cambiar)</span>
            </label>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <input
                  name="contrasena"
                  type={editMostrarContrasena ? "text" : "password"}
                  value={editForm.contrasena}
                  onChange={handleEditChange}
                  minLength={4}
                  placeholder="Minimo 4 caracteres"
                  className={inputClass + " pr-9"}
                />
                <button
                  type="button"
                  onClick={() => setEditMostrarContrasena((v) => !v)}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  tabIndex={-1}
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    {editMostrarContrasena
                      ? <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
                      : <><path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" /><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></>
                    }
                  </svg>
                </button>
              </div>
              <button
                type="button"
                onClick={() => { setEditForm((f) => ({ ...f, contrasena: generarContrasena() })); setEditMostrarContrasena(true); }}
                className="px-3 py-2 text-xs font-medium text-brand-600 bg-brand-50 rounded-lg hover:bg-brand-100 transition-colors whitespace-nowrap"
              >
                Generar
              </button>
            </div>
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button type="submit" disabled={editEnviando}
            className="w-full py-2.5 bg-brand-600 text-white rounded-lg font-medium hover:bg-brand-700 transition-colors disabled:opacity-50">
            {editEnviando ? "Guardando..." : "Guardar Cambios"}
          </button>
        </form>
      </Modal>
    </div>
  );
}

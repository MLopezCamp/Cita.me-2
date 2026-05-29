"use client";
import { useEffect, useState } from "react";
import { useAuth } from "../../hooks/useAuth";
import { pacientes } from "../../services/api";
import Modal from "../../components/Modal";

export default function PacientesPage() {
  const { user, loading: authLoading } = useAuth(["admin", "administrativo"]);
  const [lista, setLista] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);

  const [form, setForm] = useState({
    nombre: "", apellido: "", documento: "", email: "", telefono: "", fecha_nacimiento: "",
  });

  useEffect(() => {
    if (!user) return;
    cargarPacientes();
  }, [user]);

  async function cargarPacientes() {
    try {
      const data = await pacientes.listar();
      setLista(data);
    } catch (err) { setError(err.message); }
    finally { setDataLoading(false); }
  }

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setEnviando(true);
    setError("");
    try {
      await pacientes.crear(form);
      setModalOpen(false);
      setForm({ nombre: "", apellido: "", documento: "", email: "", telefono: "", fecha_nacimiento: "" });
      await cargarPacientes();
    } catch (err) { setError(err.message); }
    finally { setEnviando(false); }
  }

  if (authLoading) return <div className="text-center py-12 text-gray-400">Cargando...</div>;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-extrabold text-gray-900">Pacientes</h1>
          <p className="text-sm text-gray-500">{lista.length} registrados</p>
        </div>
        <button
          onClick={() => setModalOpen(true)}
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
          <p className="text-gray-300 text-sm">Haga clic en &quot;Nuevo Paciente&quot; para comenzar</p>
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
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} title="Nuevo Paciente">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nombre</label>
              <input name="nombre" value={form.nombre} onChange={handleChange} required
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Apellido</label>
              <input name="apellido" value={form.apellido} onChange={handleChange} required
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Documento</label>
            <input name="documento" value={form.documento} onChange={handleChange} required
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input name="email" type="email" value={form.email} onChange={handleChange} required
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Teléfono</label>
              <input name="telefono" value={form.telefono} onChange={handleChange} required
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Fecha de nacimiento</label>
              <input name="fecha_nacimiento" type="date" value={form.fecha_nacimiento} onChange={handleChange} required
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent" />
            </div>
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button type="submit" disabled={enviando}
            className="w-full py-2.5 bg-brand-600 text-white rounded-lg font-medium hover:bg-brand-700 transition-colors disabled:opacity-50">
            {enviando ? "Guardando..." : "Registrar Paciente"}
          </button>
        </form>
      </Modal>
    </div>
  );
}
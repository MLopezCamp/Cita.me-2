"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { auth } from "../../services/api";

const ROLES = [
  { value: "admin", label: "Administrador", color: "bg-gray-800" },
  { value: "doctor", label: "Doctor", color: "bg-amber-600" },
  { value: "paciente", label: "Paciente", color: "bg-sky-600" },
];

export default function LoginPage() {
  const router = useRouter();
  const [rol, setRol] = useState("paciente");
  const [form, setForm] = useState({ usuario: "", email: "", documento: "", contrasena: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const payload = { rol, contrasena: form.contrasena };
      if (rol === "admin") payload.usuario = form.usuario;
      if (rol === "doctor") payload.email = form.email;
      if (rol === "paciente") payload.documento = form.documento;

      const user = await auth.login(payload);
      localStorage.setItem("citame_user", JSON.stringify(user));

      if (user.rol === "admin") router.push("/");
      else if (user.rol === "doctor") router.push("/doctores-portal");
      else router.push("/portal");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const rolActual = ROLES.find((r) => r.value === rol);

  return (
    <div className="min-h-[80vh] flex items-center justify-center">
      <div className="w-full max-w-sm bg-white rounded-2xl border border-gray-100 p-8 shadow-sm card-animate">
        <div className="text-center mb-6">
          <h1 className="text-2xl font-extrabold text-gray-900">
            cita<span className="text-brand-600">.me</span>
          </h1>
          <p className="text-sm text-gray-500 mt-1">Ingrese a su cuenta</p>
        </div>

        <div className="flex rounded-xl overflow-hidden border border-gray-200 mb-6">
          {ROLES.map((r) => (
            <button
              key={r.value}
              type="button"
              onClick={() => { setRol(r.value); setError(""); }}
              className={`flex-1 py-2.5 text-xs font-semibold transition-all ${
                rol === r.value
                  ? `${r.color} text-white`
                  : "bg-white text-gray-500 hover:bg-gray-50"
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {rol === "admin" && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Usuario</label>
              <input name="usuario" value={form.usuario} onChange={handleChange} required
                placeholder="admin"
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-transparent" />
            </div>
          )}

          {rol === "doctor" && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email del doctor</label>
              <input name="email" type="email" value={form.email} onChange={handleChange} required
                placeholder="maria.gonzalez@medicita.com"
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent" />
            </div>
          )}

          {rol === "paciente" && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Número de documento</label>
              <input name="documento" value={form.documento} onChange={handleChange} required
                placeholder="1001234567"
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent" />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Contraseña</label>
            <input name="contrasena" type="password" value={form.contrasena} onChange={handleChange} required
              placeholder="••••••••"
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-400 focus:border-transparent" />
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">{error}</div>
          )}

          <button type="submit" disabled={loading}
            className={`w-full py-2.5 text-white rounded-lg font-medium transition-colors disabled:opacity-50 ${rolActual?.color} hover:opacity-90`}>
            {loading ? "Verificando..." : `Ingresar como ${rolActual?.label}`}
          </button>
        </form>

        <div className="mt-5 pt-4 border-t border-gray-100">
          <p className="text-xs text-gray-400 text-center mb-2">Datos de prueba:</p>
          <div className="space-y-1 text-xs text-gray-400">
            {rol === "admin" && <p className="text-center">Usuario: <span className="font-mono text-gray-600">admin</span> · Clave: <span className="font-mono text-gray-600">admin</span></p>}
            {rol === "doctor" && <p className="text-center">Email: <span className="font-mono text-gray-600">maria.gonzalez@medicita.com</span> · Clave: <span className="font-mono text-gray-600">1234</span></p>}
            {rol === "paciente" && <p className="text-center">Doc: <span className="font-mono text-gray-600">1001234567</span> · Clave: <span className="font-mono text-gray-600">1234</span></p>}
          </div>
        </div>
      </div>
    </div>
  );
}
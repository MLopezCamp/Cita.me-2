"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { auth } from "../../services/api";

const ROLES = [
  { value: "administrativo", label: "Administrativo", color: "bg-gray-800", ring: "focus:ring-gray-700" },
  { value: "doctor", label: "Doctor", color: "bg-amber-600", ring: "focus:ring-amber-500" },
];

export default function StaffPage() {
  const router = useRouter();
  const [rol, setRol] = useState("administrativo");
  const [modoAdmin, setModoAdmin] = useState(false);
  const [form, setForm] = useState({ email: "", usuario: "", contrasena: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  function cambiarRol(nuevoRol) {
    setRol(nuevoRol);
    setModoAdmin(false);
    setError("");
    setForm({ email: "", usuario: "", contrasena: "" });
  }

  function activarAdmin() {
    setRol("admin");
    setModoAdmin(true);
    setError("");
    setForm({ email: "", usuario: "", contrasena: "" });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const identifier = rol === "admin" ? form.usuario : form.email;
      const userData = await auth.login({ rol, identifier, contrasena: form.contrasena });
      localStorage.setItem("citame_user", JSON.stringify(userData));
      router.push(userData.rol === "doctor" ? "/doctores-portal" : "/");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const rolActual = ROLES.find((r) => r.value === rol) ?? { color: "bg-gray-700", ring: "focus:ring-gray-600" };

  return (
    <div className="min-h-[80vh] flex items-center justify-center">
      <div className="w-full max-w-sm bg-white rounded-2xl border border-gray-100 p-8 shadow-sm card-animate">
        <div className="text-center mb-6">
          <h1 className="text-2xl font-extrabold text-gray-900">
            cita<span className="text-gray-600">.me</span>
          </h1>
          <p className="text-sm text-gray-500 mt-1">Acceso de personal</p>
        </div>

        {/* Selector de rol (oculto en modo admin) */}
        {!modoAdmin ? (
          <div className="flex rounded-xl overflow-hidden border border-gray-200 mb-6">
            {ROLES.map((r) => (
              <button
                key={r.value}
                type="button"
                onClick={() => cambiarRol(r.value)}
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
        ) : (
          <div className="flex items-center gap-2 mb-6">
            <button
              type="button"
              onClick={() => cambiarRol("administrativo")}
              className="text-xs text-gray-400 hover:text-gray-600 transition-colors"
            >
              Volver
            </button>
            <span className="text-xs text-gray-400">/</span>
            <span className="text-xs font-semibold text-gray-700">Acceso de sistema</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {rol !== "admin" ? (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                name="email"
                type="email"
                value={form.email}
                onChange={handleChange}
                required
                autoComplete="email"
                placeholder={rol === "administrativo" ? "administrativo@clinica.com" : "doctor@clinica.com"}
                className={`w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 ${rolActual.ring} focus:border-transparent`}
              />
            </div>
          ) : (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Usuario</label>
              <input
                name="usuario"
                value={form.usuario}
                onChange={handleChange}
                required
                autoComplete="username"
                placeholder="admin"
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-700 focus:border-transparent"
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Contrasena</label>
            <input
              name="contrasena"
              type="password"
              value={form.contrasena}
              onChange={handleChange}
              required
              autoComplete="current-password"
              placeholder="••••••••"
              className={`w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 ${rolActual.ring} focus:border-transparent`}
            />
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className={`w-full py-3 text-white rounded-lg font-semibold hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed ${rolActual.color}`}
          >
            {loading ? "Ingresando..." : "Ingresar"}
          </button>
        </form>

        <div className="mt-6 pt-4 border-t border-gray-100 flex items-center justify-between text-xs text-gray-400">
          <Link href="/login" className="hover:text-gray-600 transition-colors">
            Acceso pacientes
          </Link>
          {!modoAdmin && (
            <button
              type="button"
              onClick={activarAdmin}
              className="hover:text-gray-600 transition-colors"
            >
              Acceso de sistema
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

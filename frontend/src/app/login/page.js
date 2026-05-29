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
      // El backend espera siempre el campo "identifier", sin importar el rol
      let identifier;
      if (rol === "admin") identifier = form.usuario;
      else if (rol === "doctor") identifier = form.email;
      else if (rol === "paciente") identifier = form.documento;

      const payload = { rol, identifier, contrasena: form.contrasena };
      const userData = await auth.login(payload);

      // Guardar sesión completa (incluye access_token)
      localStorage.setItem("citame_user", JSON.stringify(userData));

      // Redirigir según rol
      if (userData.rol === "admin") router.push("/");
      else if (userData.rol === "doctor") router.push("/doctores-portal");
      else if (userData.rol === "paciente") router.push("/portal");
      else router.push("/");
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

        {/* Selector de rol */}
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
          {/* Campo identificador según rol */}
          {rol === "admin" && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Usuario</label>
              <input
                name="usuario"
                value={form.usuario}
                onChange={handleChange}
                required
                autoComplete="username"
                placeholder="admin"
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-800 focus:border-transparent"
              />
            </div>
          )}

          {rol === "doctor" && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                name="email"
                type="email"
                value={form.email}
                onChange={handleChange}
                required
                autoComplete="email"
                placeholder="doctor@clinica.com"
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent"
              />
            </div>
          )}

          {rol === "paciente" && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Número de documento
              </label>
              <input
                name="documento"
                value={form.documento}
                onChange={handleChange}
                required
                autoComplete="off"
                placeholder="Ej: 1234567890"
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent"
              />
            </div>
          )}

          {/* Contraseña */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Contraseña</label>
            <input
              name="contrasena"
              type="password"
              value={form.contrasena}
              onChange={handleChange}
              required
              autoComplete="current-password"
              placeholder="••••••••"
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
            />
          </div>

          {/* Error */}
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
              {error}
            </div>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            className={`w-full py-3 text-white rounded-lg font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${rolActual.color} hover:opacity-90`}
          >
            {loading ? "Ingresando..." : "Ingresar"}
          </button>
        </form>
      </div>
    </div>
  );
}
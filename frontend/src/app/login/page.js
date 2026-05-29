"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { auth } from "../../services/api";

export default function LoginPage() {
  const router = useRouter();
  const [form, setForm] = useState({ documento: "", contrasena: "" });
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
      const userData = await auth.login({
        rol: "paciente",
        identifier: form.documento,
        contrasena: form.contrasena,
      });
      localStorage.setItem("citame_user", JSON.stringify(userData));
      router.push("/portal");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-[80vh] flex items-center justify-center">
      <div className="w-full max-w-sm bg-white rounded-2xl border border-gray-100 p-8 shadow-sm card-animate">
        <div className="text-center mb-6">
          <h1 className="text-2xl font-extrabold text-gray-900">
            cita<span className="text-sky-600">.me</span>
          </h1>
          <p className="text-sm text-gray-500 mt-1">Portal del paciente</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Numero de documento
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
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent"
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
            className="w-full py-3 bg-sky-600 text-white rounded-lg font-semibold hover:bg-sky-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Ingresando..." : "Ingresar"}
          </button>
        </form>

        <div className="mt-6 pt-4 border-t border-gray-100 text-center">
          <Link href="/staff" className="text-xs text-gray-400 hover:text-gray-600 transition-colors">
            Acceso para personal medico
          </Link>
        </div>
      </div>
    </div>
  );
}

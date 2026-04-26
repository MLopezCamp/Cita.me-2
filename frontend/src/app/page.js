"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { citas, doctores, pacientes } from "../services/api";
import { useAuth } from "../hooks/useAuth";

export default function HomePage() {
  const { user, loading } = useAuth("admin");
  const [stats, setStats] = useState({ citas: 0, doctores: 0, pacientes: 0 });
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    if (!user) return;
    async function cargar() {
      try {
        const [c, d, p] = await Promise.all([citas.listar(), doctores.listar(), pacientes.listar()]);
        setStats({ citas: c.length, doctores: d.length, pacientes: p.length });
      } catch {}
      setCargando(false);
    }
    cargar();
  }, [user]);

  if (loading) return <div className="text-center py-12 text-gray-400">Cargando...</div>;

  const tarjetas = [
    { titulo: "Pacientes", valor: stats.pacientes, color: "bg-brand-50 text-brand-600", link: "/pacientes" },
    { titulo: "Doctores", valor: stats.doctores, color: "bg-amber-50 text-amber-600", link: "/doctores" },
    { titulo: "Citas", valor: stats.citas, color: "bg-sky-50 text-sky-600", link: "/citas" },
  ];

  return (
    <div>
      <section className="mb-8">
        <h1 className="text-3xl font-extrabold text-gray-900 mb-1">
          Bienvenido, <span className="text-gray-500">{user?.nombre}</span>
        </h1>
        <p className="text-gray-500">Panel de administración de cita.me</p>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
        {tarjetas.map((t, i) => (
          <Link key={t.titulo} href={t.link}
            className="card-animate bg-white rounded-xl border border-gray-100 p-6 hover:shadow-lg transition-all group"
            style={{ animationDelay: `${i * 80}ms` }}>
            <div className={`w-11 h-11 rounded-xl flex items-center justify-center ${t.color} mb-3`}>
              <span className="text-xl font-extrabold">{cargando ? "—" : t.valor}</span>
            </div>
            <p className="text-sm font-medium text-gray-400">{t.titulo}</p>
          </Link>
        ))}
      </section>

      <section className="bg-white rounded-xl border border-gray-100 p-6">
        <h2 className="text-lg font-bold text-gray-800 mb-4">Acciones rápidas</h2>
        <div className="flex flex-wrap gap-3">
          <Link href="/nueva-cita" className="inline-flex items-center gap-2 px-5 py-2.5 bg-brand-600 text-white rounded-lg font-medium hover:bg-brand-700 transition-colors shadow-sm">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            Nueva Cita
          </Link>
          <Link href="/pacientes" className="inline-flex items-center gap-2 px-5 py-2.5 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors">
            Registrar Paciente
          </Link>
          <Link href="/doctores" className="inline-flex items-center gap-2 px-5 py-2.5 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors">
            Ver Doctores
          </Link>
        </div>
      </section>
    </div>
  );
}
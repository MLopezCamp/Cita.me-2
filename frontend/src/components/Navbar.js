"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState(null);

  useEffect(() => {
    const stored = localStorage.getItem("citame_user");
    if (stored) {
      try { setUser(JSON.parse(stored)); } catch { setUser(null); }
    } else {
      setUser(null);
    }
  }, [pathname]);

  function logout() {
    localStorage.removeItem("citame_user");
    router.push("/login");
  }

  // No logueado
  if (!user) return null;

  // Links según rol
  let links = [];
  if (user.rol === "admin") {
    links = [
      { href: "/", label: "Inicio" },
      { href: "/pacientes", label: "Pacientes" },
      { href: "/doctores", label: "Doctores" },
      { href: "/citas", label: "Citas" },
      { href: "/nueva-cita", label: "Nueva Cita" },
    ];
  } else if (user.rol === "doctor") {
    links = [
      { href: "/doctores-portal", label: "Mis Citas" },
    ];
  } else if (user.rol === "paciente") {
    links = [
      { href: "/portal", label: "Mi Panel" },
      { href: "/portal/nueva-cita", label: "Pedir Cita" },
    ];
  }

  const colores = {
    admin: "bg-gray-800",
    doctor: "bg-amber-600",
    paciente: "bg-sky-600",
  };
  const coloresTexto = {
    admin: "text-gray-800",
    doctor: "text-amber-600",
    paciente: "text-sky-600",
  };

  return (
    <nav className="bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link href={user.rol === "admin" ? "/" : user.rol === "doctor" ? "/doctores-portal" : "/portal"}
            className="flex items-center gap-2.5">
            <div className={`w-9 h-9 rounded-lg ${colores[user.rol]} flex items-center justify-center`}>
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
              </svg>
            </div>
            <span className="font-extrabold text-xl text-gray-800 tracking-tight">
              cita<span className={coloresTexto[user.rol]}>.me</span>
            </span>
          </Link>

          <div className="flex items-center gap-1">
            {links.map((link) => {
              const isActive = pathname === link.href;
              const activeClass = user.rol === "admin"
                ? "bg-gray-100 text-gray-800"
                : user.rol === "doctor"
                  ? "bg-amber-50 text-amber-700"
                  : "bg-sky-50 text-sky-700";
              return (
                <Link key={link.href} href={link.href}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive ? activeClass : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                  }`}>
                  {link.label}
                </Link>
              );
            })}
          </div>

          {/* Usuario + logout */}
          <div className="flex items-center gap-3">
            <div className="text-right hidden sm:block">
              <p className="text-sm font-medium text-gray-800">{user.nombre}</p>
              <p className="text-[10px] uppercase font-bold text-gray-400 tracking-wider">{user.rol}</p>
            </div>
            <button onClick={logout}
              className="px-3 py-2 rounded-lg text-sm text-gray-500 hover:text-red-600 hover:bg-red-50 transition-colors"
              title="Cerrar sesión">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
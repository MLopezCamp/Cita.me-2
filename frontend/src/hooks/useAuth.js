"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

/**
 * Hook de autenticacion para proteger paginas.
 *
 * Uso:
 *   useAuth()                               — cualquier rol autenticado
 *   useAuth("admin")                        — solo admin
 *   useAuth(["admin", "administrativo"])    — admin o administrativo
 *   useAuth("paciente")                     — solo paciente
 *   useAuth("doctor")                       — solo doctor
 */
export function useAuth(requiredRole = null) {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem("citame_user");

    if (!stored) {
      router.replace("/login");
      return;
    }

    let parsed;
    try {
      parsed = JSON.parse(stored);
    } catch {
      localStorage.removeItem("citame_user");
      router.replace("/login");
      return;
    }

    if (!parsed.access_token || !parsed.rol) {
      localStorage.removeItem("citame_user");
      router.replace("/login");
      return;
    }

    const allowedRoles = Array.isArray(requiredRole)
      ? requiredRole
      : requiredRole ? [requiredRole] : null;

    if (allowedRoles && !allowedRoles.includes(parsed.rol)) {
      const destinos = {
        admin: "/",
        administrativo: "/",
        doctor: "/doctores-portal",
        paciente: "/portal",
      };
      router.replace(destinos[parsed.rol] || "/login");
      return;
    }

    setUser(parsed);
    setLoading(false);
  }, [router, requiredRole]);

  function logout() {
    const esPersonal = user?.rol !== "paciente";
    localStorage.removeItem("citame_user");
    router.replace(esPersonal ? "/staff" : "/login");
  }

  return { user, loading, logout };
}

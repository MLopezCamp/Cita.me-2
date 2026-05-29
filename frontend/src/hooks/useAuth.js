"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

/**
 * Hook de autenticación para proteger páginas.
 * Lee la sesión del localStorage y redirige a /login si no hay sesión válida.
 *
 * Uso:
 *   const { user, loading, logout } = useAuth();            // cualquier rol autenticado
 *   const { user, loading, logout } = useAuth("admin");     // solo admin
 *   const { user, loading, logout } = useAuth("paciente");  // solo paciente
 *   const { user, loading, logout } = useAuth("doctor");    // solo doctor
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

    // Verificar que el objeto tiene los campos mínimos esperados
    if (!parsed.access_token || !parsed.rol) {
      localStorage.removeItem("citame_user");
      router.replace("/login");
      return;
    }

    // Verificar rol si se requiere uno específico
    if (requiredRole && parsed.rol !== requiredRole) {
      // Redirigir al portal correcto según el rol real del usuario
      const destinos = {
        admin: "/",
        doctor: "/doctores-portal",
        paciente: "/portal",
        administrativo: "/login",
      };
      router.replace(destinos[parsed.rol] || "/login");
      return;
    }

    setUser(parsed);
    setLoading(false);
  }, [router, requiredRole]);

  function logout() {
    localStorage.removeItem("citame_user");
    router.replace("/login");
  }

  return { user, loading, logout };
}
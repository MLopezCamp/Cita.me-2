import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

/**
 * Hook de autenticación para proteger páginas.
 * Lee del localStorage y redirige a /login si no hay sesión.
 *
 * Uso:
 *   const { user, loading, logout } = useAuth();           // cualquier rol
 *   const { user, loading, logout } = useAuth("admin");    // solo admin
 *   const { user, loading, logout } = useAuth("paciente"); // solo paciente
 */
export function useAuth(requiredRole = null) {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem("citame_user");
    if (!stored) {
      router.push("/login");
      return;
    }
    try {
      const parsed = JSON.parse(stored);
      if (requiredRole && parsed.rol !== requiredRole) {
        router.push("/login");
        return;
      }
      setUser(parsed);
    } catch {
      router.push("/login");
      return;
    }
    setLoading(false);
  }, [router, requiredRole]);

  function logout() {
    localStorage.removeItem("citame_user");
    router.push("/login");
  }

  return { user, loading, logout };
}
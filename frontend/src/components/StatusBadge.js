export default function StatusBadge({ estado }) {
  const estilos = {
    pendiente: "bg-amber-100 text-amber-800 border-amber-300",
    confirmada: "bg-emerald-100 text-emerald-800 border-emerald-300",
    cancelada: "bg-red-100 text-red-800 border-red-300",
    completada: "bg-blue-100 text-blue-800 border-blue-300",
  };

  const clase = estilos[estado] || "bg-gray-100 text-gray-800 border-gray-300";

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${clase}`}>
      {estado.charAt(0).toUpperCase() + estado.slice(1)}
    </span>
  );
}
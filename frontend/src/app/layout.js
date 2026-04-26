import "./globals.css";
import Navbar from "../components/Navbar";

export const metadata = {
  title: "cita.me — Citas Médicas",
  description: "Sistema de reservas de citas médicas",
};

export default function RootLayout({ children }) {
  return (
    <html lang="es">
      <body className="min-h-screen flex flex-col">
        <Navbar />
        <main className="flex-1 max-w-6xl mx-auto px-4 py-8 w-full">
          {children}
        </main>
        <footer className="text-center text-xs text-gray-400 py-5 border-t border-gray-100 mt-auto">
          © {new Date().getFullYear()} Todos los derechos reservados, Cotecnova.
        </footer>
      </body>
    </html>
  );
}
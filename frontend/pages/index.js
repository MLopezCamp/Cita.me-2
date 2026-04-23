import { useState } from 'react';
import axios from 'axios';

export default function Home() {
  const [formData, setFormData] = useState({
    nombre: '',
    documento: '',
    email: ''
  });
  const [cita, setCita] = useState({
    paciente_id: '',
    medico_id: '',
    fecha: '',
    hora: '',
    motivo: ''
  });
  const [mensaje, setMensaje] = useState('');

  const handlePacienteChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleCitaChange = (e) => {
    setCita({ ...cita, [e.target.name]: e.target.value });
  };

  const crearPaciente = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post('http://localhost:8000/pacientes', formData);
      setMensaje(`Paciente creado con ID: ${res.data.id}`);
      setCita({ ...cita, paciente_id: res.data.id });
    } catch (error) {
      setMensaje('Error al crear paciente');
    }
  };

  const crearCita = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post('http://localhost:8000/citas', cita);
      setMensaje(`Cita agendada con ID: ${res.data.id}. Recibirá un correo de confirmación.`);
    } catch (error) {
      setMensaje(error.response?.data?.detail || 'Error al agendar cita');
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>Sistema de Citas Médicas</h1>

      <h2>Registrar Paciente</h2>
      <form onSubmit={crearPaciente}>
        <input name="nombre" placeholder="Nombre" onChange={handlePacienteChange} required /><br />
        <input name="documento" placeholder="Documento" onChange={handlePacienteChange} required /><br />
        <input name="email" placeholder="Email" type="email" onChange={handlePacienteChange} required /><br />
        <button type="submit">Crear Paciente</button>
      </form>

      <h2>Agendar Cita</h2>
      <form onSubmit={crearCita}>
        <input name="paciente_id" placeholder="ID del Paciente" onChange={handleCitaChange} required /><br />
        <input name="medico_id" placeholder="ID del Médico" onChange={handleCitaChange} required /><br />
        <input name="fecha" placeholder="Fecha (YYYY-MM-DD)" onChange={handleCitaChange} required /><br />
        <input name="hora" placeholder="Hora (HH:MM)" onChange={handleCitaChange} required /><br />
        <textarea name="motivo" placeholder="Motivo" onChange={handleCitaChange}></textarea><br />
        <button type="submit">Agendar Cita</button>
      </form>

      {mensaje && <p>{mensaje}</p>}
    </div>
  );
}
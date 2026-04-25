import axios from 'axios';

// Configuramos la URL base del backend
// En producción, esto debería venir de una variable de entorno
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;

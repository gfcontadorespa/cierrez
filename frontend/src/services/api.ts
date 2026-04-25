import axios from 'axios';

// Configuramos la URL base del backend
// En producción, esto debería venir de una variable de entorno
const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;

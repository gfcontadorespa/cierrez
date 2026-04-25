import React from 'react';
import { useNavigate } from 'react-router-dom';
import { GoogleLogin } from '@react-oauth/google';
import api from '../services/api';

const Login: React.FC = () => {
  const navigate = useNavigate();

  const handleGoogleSuccess = async (credentialResponse: any) => {
    try {
      // Enviar el token de Google al backend para verificación
      const res = await api.post('/auth/google', {
        token: credentialResponse.credential
      });
      
      // Guardar el token de sesión (simulado por ahora)
      localStorage.setItem('token', res.data.access_token);
      localStorage.setItem('user', JSON.stringify(res.data.user));
      
      navigate('/dashboard');
    } catch (error: any) {
      console.error('Error al iniciar sesión:', error);
      const backendMessage = error.response?.data?.detail || error.message || 'Desconocido';
      alert('Error al iniciar sesión: ' + backendMessage);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="mt-6 text-center text-3xl font-extrabold text-slate-900">
          Validador SaaS
        </h2>
        <p className="mt-2 text-center text-sm text-slate-600">
          Inicia sesión de forma segura con tu cuenta de Google
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <div className="flex justify-center">
            <GoogleLogin
              onSuccess={handleGoogleSuccess}
              onError={() => {
                console.error('Login Failed');
                alert('Fallo en el inicio de sesión de Google');
              }}
              useOneTap
              theme="filled_blue"
              shape="rectangular"
              text="continue_with"
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;

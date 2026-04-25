import React from 'react';
import { useNavigate } from 'react-router-dom';
import { GoogleLogin } from '@react-oauth/google';
import { useMsal } from '@azure/msal-react';
import { loginRequest } from '../authConfig';
import api from '../services/api';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const { instance } = useMsal();

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

  const handleMicrosoftLogin = async () => {
    try {
      const loginResponse = await instance.loginPopup(loginRequest);
      
      // Enviar el token de Microsoft al backend para verificación
      const res = await api.post('/auth/microsoft', {
        token: loginResponse.idToken
      });
      
      // Guardar el token de sesión
      localStorage.setItem('token', res.data.access_token);
      localStorage.setItem('user', JSON.stringify(res.data.user));
      
      navigate('/dashboard');
    } catch (error: any) {
      console.error('Error al iniciar sesión con Microsoft:', error);
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
          Inicia sesión de forma segura con tu cuenta de Google o Microsoft
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <div className="flex flex-col items-center space-y-4">
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
            
            <div className="relative w-full flex items-center py-2">
              <div className="flex-grow border-t border-slate-300"></div>
              <span className="flex-shrink-0 mx-4 text-slate-400 text-sm">o</span>
              <div className="flex-grow border-t border-slate-300"></div>
            </div>

            <button
              onClick={handleMicrosoftLogin}
              className="w-full max-w-[200px] flex items-center justify-center px-4 py-2 border border-slate-300 shadow-sm text-sm font-medium rounded-md text-slate-700 bg-white hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
            >
              <svg className="w-5 h-5 mr-2" viewBox="0 0 21 21" xmlns="http://www.w3.org/2000/svg">
                <rect x="1" y="1" width="9" height="9" fill="#f25022"/>
                <rect x="1" y="11" width="9" height="9" fill="#00a4ef"/>
                <rect x="11" y="1" width="9" height="9" fill="#7fba00"/>
                <rect x="11" y="11" width="9" height="9" fill="#ffb900"/>
              </svg>
              Continuar con Microsoft
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;

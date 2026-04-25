import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { GoogleOAuthProvider } from '@react-oauth/google';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import PaymentMethods from './pages/PaymentMethods';
import Companies from './pages/admin/Companies';
import BankAccounts from './pages/admin/BankAccounts';
import GlobalUsers from './pages/admin/GlobalUsers';
import CierresZ from './pages/CierresZ';
import CierreZForm from './pages/CierreZForm';
import CierreZDetails from './pages/CierreZDetails';
import Branches from './pages/admin/Branches';
import Onboarding from './pages/Onboarding';

function App() {
  return (
    <GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID || 'YOUR_GOOGLE_CLIENT_ID'}>
      <Router>
        <Routes>
          {/* Ruta pública */}
          <Route path="/" element={<Login />} />
          <Route path="/login" element={<Navigate to="/" replace />} />

          {/* Rutas protegidas (Envueltas en el Layout) */}
          <Route element={<Layout />}>
            {/* Operativo */}
            <Route path="/onboarding" element={<Onboarding />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/cierres" element={<CierresZ />} />
            <Route path="/cierres/nuevo" element={<CierreZForm />} />
            <Route path="/cierres/:id" element={<CierreZDetails />} />
            
            {/* Configuración de Compañía (Admin Local) */}
            <Route path="/settings/payment-methods" element={<PaymentMethods />} />
            <Route path="/settings/bank-accounts" element={<BankAccounts />} />
            <Route path="/settings/branches" element={<Branches />} />
            
            {/* Global Admin */}
            <Route path="/admin/companies" element={<Companies />} />
            <Route path="/admin/users" element={<GlobalUsers />} />
          </Route>

          {/* Ruta comodín para redirigir a login si no existe */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </GoogleOAuthProvider>
  );
}

export default App;

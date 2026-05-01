import React, { useState, useEffect } from 'react';
import { Plus, Receipt, FileText, CheckCircle2 } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api';

interface Cierre {
  id: number;
  z_number: string;
  date_closed: string;
  total_sales: number;
  total_receipt: number;
  status: string;
  difference_amount: number;
  workflow_status: string;
}

const CierresZ: React.FC = () => {
  const navigate = useNavigate();
  const [cierres, setCierres] = useState<Cierre[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCierres();
  }, []);

  const fetchCierres = async () => {
    try {
      setLoading(true);
      const userStr = localStorage.getItem('user');
      const user = userStr ? JSON.parse(userStr) : {};
      const activeCompanyIdStr = localStorage.getItem('active_company_id');
      const companyId = activeCompanyIdStr ? parseInt(activeCompanyIdStr) : user.company_id || 1;
      const response = await api.get(`/cierres?company_id=${companyId}`);
      setCierres(response.data);
    } catch (error) {
      console.error('Error fetching cierres:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="md:flex md:items-center md:justify-between mb-6">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-slate-900 sm:text-3xl flex items-center">
            <Receipt className="mr-3 h-8 w-8 text-slate-500" />
            Cierres Z
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Historial de cierres de caja y reportes Z registrados.
          </p>
        </div>
        <div className="mt-4 flex md:mt-0 md:ml-4">
          <Link
            to="/cierres/nuevo"
            className="ml-3 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
          >
            <Plus className="mr-2 h-4 w-4" /> Registrar Cierre Z
          </Link>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-slate-500">Cargando cierres...</div>
        ) : (
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Número Z</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Fecha</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Total Ventas</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Total Cierre (Con Imp.)</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Estado Flujo</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Cuadre</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-slate-200">
              {cierres.map((cierre) => (
                <tr key={cierre.id} onClick={() => navigate(`/cierres/${cierre.id}`)} className="hover:bg-slate-50 cursor-pointer">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-900 flex items-center">
                    <FileText className="mr-2 h-4 w-4 text-slate-400" />
                    {cierre.z_number}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">{cierre.date_closed}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-slate-600">${cierre.total_sales.toFixed(2)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-mono font-bold text-slate-800">${cierre.total_receipt.toFixed(2)}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {cierre.workflow_status === 'approved' ? (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        Aprobado
                      </span>
                    ) : cierre.workflow_status === 'submitted' ? (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        Enviado
                      </span>
                    ) : cierre.workflow_status === 'rejected' ? (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        Devuelto
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                        Borrador
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {cierre.status === 'unbalanced' ? (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        Descuadrado (${Math.abs(cierre.difference_amount).toFixed(2)})
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        <CheckCircle2 className="mr-1 h-3 w-3" /> Cuadrado
                      </span>
                    )}
                  </td>
                </tr>
              ))}
              {cierres.length === 0 && (
                <tr><td colSpan={6} className="px-6 py-8 text-center text-slate-500">No hay cierres registrados. Haz clic en "Registrar Cierre Z" para empezar.</td></tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default CierresZ;

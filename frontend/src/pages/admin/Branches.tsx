import React, { useState, useEffect } from 'react';
import { Plus, Store, CheckCircle2, XCircle } from 'lucide-react';
import api from '../../services/api';

interface Branch {
  id: number;
  name: string;
  active: boolean;
}

const Branches: React.FC = () => {
  const [branches, setBranches] = useState<Branch[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newBranch, setNewBranch] = useState({ company_id: 1, name: '' });

  useEffect(() => {
    fetchBranches();
  }, []);

  const fetchBranches = async () => {
    try {
      setLoading(true);
      const response = await api.get('/branches?company_id=1');
      setBranches(response.data);
    } catch (error) {
      console.error('Error fetching branches:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateBranch = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await api.post('/branches', newBranch);
      setBranches([response.data, ...branches]);
      setIsModalOpen(false);
      setNewBranch({ company_id: 1, name: '' });
    } catch (error) {
      console.error('Error creating branch:', error);
      alert('Hubo un error al crear la sucursal');
    }
  };

  return (
    <div>
      <div className="md:flex md:items-center md:justify-between mb-6">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-slate-900 sm:text-3xl flex items-center">
            <Store className="mr-3 h-8 w-8 text-slate-500" />
            Sucursales
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Gestiona los locales o sucursales de la empresa.
          </p>
        </div>
        <div className="mt-4 flex md:mt-0 md:ml-4">
          <button
            onClick={() => setIsModalOpen(true)}
            className="ml-3 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
          >
            <Plus className="mr-2 h-4 w-4" /> Nueva Sucursal
          </button>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-slate-500">Cargando sucursales...</div>
        ) : (
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Nombre de la Sucursal</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Estado</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-slate-200">
              {branches.map((branch) => (
                <tr key={branch.id} className="hover:bg-slate-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-900">{branch.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {branch.active ? (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        <CheckCircle2 className="mr-1 h-3 w-3" /> Activa
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        <XCircle className="mr-1 h-3 w-3" /> Inactiva
                      </span>
                    )}
                  </td>
                </tr>
              ))}
              {branches.length === 0 && (
                <tr><td colSpan={2} className="px-6 py-8 text-center text-slate-500">No hay sucursales registradas.</td></tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-slate-500 bg-opacity-75 transition-opacity" onClick={() => setIsModalOpen(false)}></div>
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen">&#8203;</span>
            <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-slate-900 mb-4">Añadir Nueva Sucursal</h3>
              <form onSubmit={handleCreateBranch} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700">Nombre de la Sucursal</label>
                  <input type="text" required className="mt-1 block w-full h-10 border border-slate-300 rounded-md shadow-sm py-2 px-3 focus:ring-blue-500 focus:border-blue-500 sm:text-sm" value={newBranch.name} onChange={e => setNewBranch({...newBranch, name: e.target.value})} placeholder="Ej: Sucursal Costa del Este" />
                </div>
                <div className="mt-5 sm:grid sm:grid-cols-2 sm:gap-3">
                  <button type="submit" className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 sm:col-start-2 sm:text-sm">Guardar</button>
                  <button type="button" onClick={() => setIsModalOpen(false)} className="mt-3 w-full inline-flex justify-center rounded-md border border-slate-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-slate-700 hover:bg-slate-50 sm:mt-0 sm:col-start-1 sm:text-sm">Cancelar</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Branches;

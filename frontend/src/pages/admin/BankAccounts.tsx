import React, { useState, useEffect } from 'react';
import { Plus, Landmark, CheckCircle2, XCircle } from 'lucide-react';
import api from '../../services/api';

interface BankAccount {
  id: number;
  company_id: number;
  name: string;
  account_number: string;
  accounting_code: string;
  active: boolean;
}

const BankAccounts: React.FC = () => {
  const [accounts, setAccounts] = useState<BankAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  // Asumimos company_id = 1 por ahora hasta tener selector de compañía
  const [newAccount, setNewAccount] = useState({ company_id: 1, name: '', account_number: '', accounting_code: '' });

  useEffect(() => {
    fetchAccounts();
  }, []);

  const fetchAccounts = async () => {
    try {
      setLoading(true);
      const response = await api.get('/bank_accounts?company_id=1');
      setAccounts(response.data);
    } catch (error) {
      console.error('Error fetching bank accounts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await api.post('/bank_accounts', newAccount);
      setAccounts([response.data, ...accounts]);
      setIsModalOpen(false);
      setNewAccount({ company_id: 1, name: '', account_number: '', accounting_code: '' });
    } catch (error) {
      console.error('Error creating bank account:', error);
      alert('Hubo un error al crear la cuenta');
    }
  };

  return (
    <div>
      <div className="md:flex md:items-center md:justify-between mb-6">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-slate-900 sm:text-3xl flex items-center">
            <Landmark className="mr-3 h-8 w-8 text-slate-500" />
            Cuentas Bancarias y Caja
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Gestiona las cuentas destino y sus códigos contables (Ej: Banco General, Caja de Venta).
          </p>
        </div>
        <div className="mt-4 flex md:mt-0 md:ml-4">
          <button
            onClick={() => setIsModalOpen(true)}
            className="ml-3 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
          >
            <Plus className="mr-2 h-4 w-4" /> Nueva Cuenta
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-slate-500">Cargando cuentas...</div>
        ) : (
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Nombre de Cuenta</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Número (Opcional)</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Código Contable</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Estado</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-slate-200">
              {accounts.map((acc) => (
                <tr key={acc.id} className="hover:bg-slate-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-900">{acc.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">{acc.account_number || '-'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-slate-600">{acc.accounting_code || '-'}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {acc.active ? (
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
              {accounts.length === 0 && (
                <tr><td colSpan={4} className="px-6 py-8 text-center text-slate-500">No hay cuentas registradas.</td></tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {/* Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-slate-500 bg-opacity-75 transition-opacity" onClick={() => setIsModalOpen(false)}></div>
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen">&#8203;</span>
            <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-slate-900 mb-4">Añadir Cuenta de Banco / Caja</h3>
              <form onSubmit={handleCreateAccount} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700">Nombre (Ej: Banco General, Caja Fuerte)</label>
                  <input type="text" required className="mt-1 block w-full h-10 border border-slate-300 rounded-md shadow-sm py-2 px-3 focus:ring-blue-500 focus:border-blue-500 sm:text-sm" value={newAccount.name} onChange={e => setNewAccount({...newAccount, name: e.target.value})} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700">Número de Cuenta (Opcional)</label>
                  <input type="text" className="mt-1 block w-full h-10 border border-slate-300 rounded-md shadow-sm py-2 px-3 focus:ring-blue-500 focus:border-blue-500 sm:text-sm" value={newAccount.account_number} onChange={e => setNewAccount({...newAccount, account_number: e.target.value})} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700">Código Contable (Ej: 1.0.0.1)</label>
                  <input type="text" className="mt-1 block w-full h-10 border border-slate-300 rounded-md shadow-sm py-2 px-3 focus:ring-blue-500 focus:border-blue-500 sm:text-sm" value={newAccount.accounting_code} onChange={e => setNewAccount({...newAccount, accounting_code: e.target.value})} />
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

export default BankAccounts;

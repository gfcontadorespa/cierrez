import React, { useState, useEffect } from 'react';
import { Plus, Building2, CheckCircle2, XCircle, Trash2 } from 'lucide-react';
import api from '../../services/api';

interface Company {
  id: number;
  name: string;
  ruc: string;
  active: boolean;
}

const Companies: React.FC = () => {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newCompany, setNewCompany] = useState({ name: '', ruc: '' });

  // User Management State
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);
  const [isUsersModalOpen, setIsUsersModalOpen] = useState(false);
  const [companyUsers, setCompanyUsers] = useState<any[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [newUserEmail, setNewUserEmail] = useState('');
  const [newUserRole, setNewUserRole] = useState('admin');

  useEffect(() => {
    fetchCompanies();
  }, []);

  const fetchCompanies = async () => {
    try {
      setLoading(true);
      const response = await api.get('/companies');
      setCompanies(response.data);
    } catch (error) {
      console.error('Error fetching companies:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCompany = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await api.post('/companies', newCompany);
      setCompanies([response.data, ...companies]);
      setIsModalOpen(false);
      setNewCompany({ name: '', ruc: '' });
    } catch (error) {
      console.error('Error creating company:', error);
      alert('Hubo un error al crear la compañía');
    }
  };

  const openUsersModal = async (company: Company) => {
    setSelectedCompany(company);
    setIsUsersModalOpen(true);
    setLoadingUsers(true);
    try {
      const response = await api.get(`/companies/${company.id}/users`);
      setCompanyUsers(response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
    } finally {
      setLoadingUsers(false);
    }
  };

  const handleInviteUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCompany) return;
    try {
      await api.post(`/companies/${selectedCompany.id}/users`, {
        email: newUserEmail,
        role: newUserRole,
        branch_ids: []
      });
      // Refresh user list
      openUsersModal(selectedCompany);
      setNewUserEmail('');
      alert('Invitación enviada exitosamente por correo.');
    } catch (error: any) {
      console.error('Error inviting user:', error);
      alert('Error al invitar usuario: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleRevokeUser = async (userId: number, userName: string) => {
    if (!selectedCompany) return;
    if (!window.confirm(`¿Estás seguro de que deseas revocar el acceso a ${userName}?`)) {
      return;
    }
    try {
      await api.delete(`/companies/${selectedCompany.id}/users/${userId}`);
      openUsersModal(selectedCompany);
    } catch (error: any) {
      console.error('Error revoking user:', error);
      alert('Error al revocar usuario: ' + (error.response?.data?.detail || error.message));
    }
  };

  return (
    <div>
      <div className="md:flex md:items-center md:justify-between mb-6">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-slate-900 sm:text-3xl sm:truncate flex items-center">
            <Building2 className="mr-3 h-8 w-8 text-slate-500" />
            Gestión de Compañías
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Administración global de los clientes (tenants) del sistema.
          </p>
        </div>
        <div className="mt-4 flex md:mt-0 md:ml-4">
          <button
            onClick={() => setIsModalOpen(true)}
            type="button"
            className="ml-3 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <Plus className="mr-2 h-4 w-4" />
            Nueva Compañía
          </button>
        </div>
      </div>

      {/* Main Table */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-slate-500">Cargando compañías...</div>
        ) : (
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  ID
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Nombre
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  RUC
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                  Estado
                </th>
                <th scope="col" className="relative px-6 py-3">
                  <span className="sr-only">Acciones</span>
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-slate-200">
              {companies.map((company) => (
                <tr key={company.id} className="hover:bg-slate-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                    #{company.id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-slate-900">{company.name}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                    {company.ruc}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {company.active ? (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        <CheckCircle2 className="mr-1 h-3 w-3" /> Activa
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        <XCircle className="mr-1 h-3 w-3" /> Inactiva
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button onClick={() => openUsersModal(company)} className="text-blue-600 hover:text-blue-900 mr-4">Usuarios</button>
                    <button className="text-slate-600 hover:text-slate-900">Editar</button>
                  </td>
                </tr>
              ))}
              {companies.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-slate-500">
                    No hay compañías registradas.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {/* Simple Modal for New Company */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-slate-500 bg-opacity-75 transition-opacity" onClick={() => setIsModalOpen(false)}></div>
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen">&#8203;</span>
            <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
              <div>
                <h3 className="text-lg leading-6 font-medium text-slate-900 mb-4">
                  Crear Nueva Compañía
                </h3>
                <form onSubmit={handleCreateCompany}>
                  <div className="space-y-4">
                    <div>
                      <label htmlFor="name" className="block text-sm font-medium text-slate-700">Nombre de la Compañía</label>
                      <input
                        type="text"
                        id="name"
                        required
                        className="mt-1 block w-full h-10 border border-slate-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                        value={newCompany.name}
                        onChange={(e) => setNewCompany({...newCompany, name: e.target.value})}
                      />
                    </div>
                    <div>
                      <label htmlFor="ruc" className="block text-sm font-medium text-slate-700">RUC</label>
                      <input
                        type="text"
                        id="ruc"
                        required
                        className="mt-1 block w-full h-10 border border-slate-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                        value={newCompany.ruc}
                        onChange={(e) => setNewCompany({...newCompany, ruc: e.target.value})}
                      />
                    </div>
                  </div>
                  <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
                    <button
                      type="submit"
                      className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:col-start-2 sm:text-sm"
                    >
                      Guardar
                    </button>
                    <button
                      type="button"
                      onClick={() => setIsModalOpen(false)}
                      className="mt-3 w-full inline-flex justify-center rounded-md border border-slate-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-slate-700 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:col-start-1 sm:text-sm"
                    >
                      Cancelar
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Users Management Modal */}
      {isUsersModalOpen && selectedCompany && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-slate-500 bg-opacity-75 transition-opacity" onClick={() => setIsUsersModalOpen(false)}></div>
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen">&#8203;</span>
            <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-3xl sm:w-full sm:p-6">
              
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg leading-6 font-bold text-slate-900">
                  Usuarios de {selectedCompany.name}
                </h3>
                <button onClick={() => setIsUsersModalOpen(false)} className="text-slate-400 hover:text-slate-500">
                  <XCircle className="h-6 w-6" />
                </button>
              </div>

              {/* Form to invite user */}
              <div className="bg-slate-50 p-4 rounded-lg border border-slate-200 mb-6">
                <h4 className="text-sm font-medium text-slate-900 mb-3">Invitar Nuevo Usuario</h4>
                <form onSubmit={handleInviteUser} className="flex gap-4 items-end">
                  <div className="flex-1">
                    <label className="block text-xs font-medium text-slate-700">Correo Electrónico</label>
                    <input
                      type="email"
                      required
                      className="mt-1 block w-full h-10 border border-slate-300 rounded-md shadow-sm px-3 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      value={newUserEmail}
                      onChange={(e) => setNewUserEmail(e.target.value)}
                      placeholder="usuario@empresa.com"
                    />
                  </div>
                  <div className="w-48">
                    <label className="block text-xs font-medium text-slate-700">Rol</label>
                    <select
                      className="mt-1 block w-full h-10 border border-slate-300 rounded-md shadow-sm px-3 focus:ring-blue-500 focus:border-blue-500 sm:text-sm bg-white"
                      value={newUserRole}
                      onChange={(e) => setNewUserRole(e.target.value)}
                    >
                      <option value="admin">Administrador (Tenant)</option>
                      <option value="user">Usuario Básico</option>
                    </select>
                  </div>
                  <button
                    type="submit"
                    className="h-10 inline-flex items-center px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
                  >
                    Enviar Invitación
                  </button>
                </form>
              </div>

              {/* User List */}
              <div className="border border-slate-200 rounded-md overflow-hidden">
                <table className="min-w-full divide-y divide-slate-200">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Nombre</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Correo</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Rol</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-slate-500 uppercase">Acciones</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-slate-200">
                    {loadingUsers ? (
                      <tr><td colSpan={3} className="px-4 py-4 text-center text-sm text-slate-500">Cargando...</td></tr>
                    ) : companyUsers.length === 0 ? (
                      <tr><td colSpan={4} className="px-4 py-4 text-center text-sm text-slate-500">No hay usuarios asignados a esta compañía.</td></tr>
                    ) : (
                      companyUsers.map(user => (
                        <tr key={user.id}>
                          <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-slate-900">{user.name}</td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-slate-500">{user.email}</td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm">
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 mr-2">
                              {user.role}
                            </span>
                            {!user.confirmed && (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800">
                                Pendiente
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap text-right text-sm font-medium">
                            <button 
                              onClick={() => handleRevokeUser(user.id, user.name)}
                              className="text-red-500 hover:text-red-700 transition-colors"
                              title="Revocar acceso"
                            >
                              <Trash2 className="h-5 w-5 inline" />
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>

            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Companies;

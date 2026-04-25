import React, { useState, useEffect } from 'react';
import { Users, UserPlus, Shield, XCircle } from 'lucide-react';
import api from '../../services/api';

const TeamUsers: React.FC = () => {
  const [teamUsers, setTeamUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newUserEmail, setNewUserEmail] = useState('');
  const [newUserRole, setNewUserRole] = useState('user');
  const [companyId, setCompanyId] = useState<number | null>(null);

  useEffect(() => {
    // Obtener company_id del usuario conectado
    const userStr = localStorage.getItem('user');
    if (userStr) {
      const user = JSON.parse(userStr);
      if (user.company_id) {
        setCompanyId(user.company_id);
        fetchTeamUsers(user.company_id);
      } else {
        setLoading(false);
      }
    } else {
      setLoading(false);
    }
  }, []);

  const fetchTeamUsers = async (cid: number) => {
    try {
      setLoading(true);
      const response = await api.get(`/companies/${cid}/users`);
      setTeamUsers(response.data);
    } catch (error) {
      console.error('Error fetching team users:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleInviteUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!companyId) return;
    try {
      await api.post(`/companies/${companyId}/users`, {
        email: newUserEmail,
        role: newUserRole,
        branch_ids: []
      });
      // Refresh user list
      fetchTeamUsers(companyId);
      setNewUserEmail('');
      setIsModalOpen(false);
      alert('Invitación enviada exitosamente por correo.');
    } catch (error: any) {
      console.error('Error inviting user:', error);
      alert('Error al invitar usuario: ' + (error.response?.data?.detail || error.message));
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-slate-500">Cargando tu equipo...</div>;
  }

  if (!companyId) {
    return (
      <div className="p-8 text-center bg-white shadow rounded-lg">
        <Shield className="mx-auto h-12 w-12 text-slate-400 mb-4" />
        <h3 className="text-lg font-medium text-slate-900">Acceso Restringido</h3>
        <p className="mt-2 text-slate-500">No tienes una compañía asignada. Contacta al administrador global.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="md:flex md:items-center md:justify-between mb-6">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-slate-900 sm:text-3xl sm:truncate flex items-center">
            <Users className="mr-3 h-8 w-8 text-slate-500" />
            Mi Equipo
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Gestiona los usuarios y roles de tu compañía.
          </p>
        </div>
        <div className="mt-4 flex md:mt-0 md:ml-4">
          <button
            onClick={() => setIsModalOpen(true)}
            type="button"
            className="ml-3 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
          >
            <UserPlus className="mr-2 h-4 w-4" />
            Invitar Usuario
          </button>
        </div>
      </div>

      {/* Main Table */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50">
            <tr>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                Nombre
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                Correo Electrónico
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                Rol
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                Estado
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-slate-200">
            {teamUsers.map((user) => (
              <tr key={user.id} className="hover:bg-slate-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-slate-900">{user.name}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                  {user.email}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    {user.role}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${user.active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                    {user.active ? 'Activo' : 'Inactivo'}
                  </span>
                </td>
              </tr>
            ))}
            {teamUsers.length === 0 && (
              <tr>
                <td colSpan={4} className="px-6 py-8 text-center text-slate-500">
                  No hay usuarios registrados en tu equipo.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Invite User Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-slate-500 bg-opacity-75 transition-opacity" onClick={() => setIsModalOpen(false)}></div>
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen">&#8203;</span>
            <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg leading-6 font-bold text-slate-900">
                  Invitar a tu Equipo
                </h3>
                <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-500">
                  <XCircle className="h-6 w-6" />
                </button>
              </div>
              <form onSubmit={handleInviteUser}>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700">Correo Electrónico</label>
                    <input
                      type="email"
                      required
                      className="mt-1 block w-full h-10 border border-slate-300 rounded-md shadow-sm px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      value={newUserEmail}
                      onChange={(e) => setNewUserEmail(e.target.value)}
                      placeholder="usuario@tuempresa.com"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700">Rol</label>
                    <select
                      className="mt-1 block w-full h-10 border border-slate-300 rounded-md shadow-sm px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm bg-white"
                      value={newUserRole}
                      onChange={(e) => setNewUserRole(e.target.value)}
                    >
                      <option value="admin">Administrador</option>
                      <option value="user">Usuario Básico / Cajero</option>
                    </select>
                  </div>
                </div>
                <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
                  <button
                    type="submit"
                    className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 sm:col-start-2 sm:text-sm"
                  >
                    Enviar Invitación
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsModalOpen(false)}
                    className="mt-3 w-full inline-flex justify-center rounded-md border border-slate-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-slate-700 hover:bg-slate-50 sm:mt-0 sm:col-start-1 sm:text-sm"
                  >
                    Cancelar
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TeamUsers;

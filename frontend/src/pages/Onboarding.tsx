import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Building2, Store, Landmark, CreditCard, Users, Hash, BrainCircuit, CheckCircle2, ArrowRight, ArrowLeft } from 'lucide-react';
import api from '../services/api';

const STEPS = [
  { id: 1, name: 'Empresa', icon: Building2 },
  { id: 2, name: 'Sucursales', icon: Store },
  { id: 3, name: 'Cuentas', icon: Landmark },
  { id: 4, name: 'Formas de Pago', icon: CreditCard },
  { id: 5, name: 'Usuarios', icon: Users },
  { id: 6, name: 'Secuencias', icon: Hash },
  { id: 7, name: 'Inteligencia Artificial', icon: BrainCircuit }
];

const Onboarding: React.FC = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  
  // Estado Global del Wizard
  const [companyId, setCompanyId] = useState<number | null>(null);
  
  // Paso 1: Empresa
  const [companyData, setCompanyData] = useState({ name: '', ruc: '' });
  
  // Paso 2: Sucursales
  const [branches, setBranches] = useState<{name: string, id?: number}[]>([{ name: 'Casa Matriz' }]);
  
  // Paso 3: Bancos
  const [bankAccounts, setBankAccounts] = useState<{name: string, account_number: string, id?: number}[]>([
    { name: 'Banco General', account_number: '' }
  ]);
  
  // Paso 4: Formas de Pago
  const [paymentMethods, setPaymentMethods] = useState<{name: string, bank_account_id: string}[]>([
    { name: 'Visa', bank_account_id: '' },
    { name: 'Efectivo', bank_account_id: '' }
  ]);
  
  // Paso 5: Usuarios
  const [users, setUsers] = useState<{email: string, role: string, branch_ids: number[]}[]>([
    { email: '', role: 'user', branch_ids: [] }
  ]);

  // Paso 6: Secuencias
  const [sequenceSettings, setSequenceSettings] = useState({
    z_sequence_type: 'manual',
    z_current_sequence: 0
  });

  // Paso 7: AI
  const [useAI, setUseAI] = useState(false);

  // Handlers para cada paso
  const handleNext = async () => {
    try {
      setLoading(true);
      
      if (currentStep === 1) {
        if (!companyData.name || !companyData.ruc) return alert("Completa los datos");
        // Si ya existe companyId, tal vez estemos regresando, no la creamos de nuevo para evitar duplicados en este MVP
        if (!companyId) {
          const res = await api.post('/companies', companyData);
          setCompanyId(res.data.id);
        }
      }
      
      if (currentStep === 2) {
        if (!companyId) return;
        const newBranches = [];
        for (const b of branches) {
          if (b.name) {
            const res = await api.post('/branches', { company_id: companyId, name: b.name });
            newBranches.push({ ...b, id: res.data.id });
          }
        }
        setBranches(newBranches);
      }
      
      if (currentStep === 3) {
        if (!companyId) return;
        const newBanks = [];
        for (const b of bankAccounts) {
          if (b.name) {
            const res = await api.post('/bank_accounts', { company_id: companyId, name: b.name, account_number: b.account_number });
            newBanks.push({...b, id: res.data.id});
          }
        }
        setBankAccounts(newBanks);
      }
      
      if (currentStep === 4) {
        if (!companyId) return;
        for (const p of paymentMethods) {
          if (p.name && p.bank_account_id) {
            await api.post('/payment_methods', { company_id: companyId, name: p.name, bank_account_id: parseInt(p.bank_account_id) });
          }
        }
      }

      if (currentStep === 5) {
        if (!companyId) return;
        for (const u of users) {
          if (u.email) {
            await api.post(`/companies/${companyId}/users`, { email: u.email, role: u.role, branch_ids: u.branch_ids });
          }
        }
      }

      if (currentStep === 6) {
        if (!companyId) return;
        await api.put(`/companies/${companyId}`, sequenceSettings);
      }

      if (currentStep === 7) {
        if (!companyId) return;
        await api.put(`/companies/${companyId}`, { use_ai_validation: useAI });
        // Fin del Onboarding
        navigate('/dashboard');
        return;
      }

      setCurrentStep(prev => prev + 1);
    } catch (error) {
      console.error(error);
      alert('Hubo un error procesando este paso.');
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) setCurrentStep(prev => prev - 1);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Header Wizard */}
      <div className="bg-white shadow-sm border-b border-slate-200">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-bold text-slate-900 flex items-center">
              <Building2 className="mr-2 text-blue-600 h-6 w-6" />
              Configuración Inicial (SaaS Onboarding)
            </h1>
            <span className="text-sm font-medium text-slate-500">Paso {currentStep} de 7</span>
          </div>
          
          {/* Progress Bar */}
          <div className="mt-6 flex justify-between relative">
            <div className="absolute top-1/2 left-0 w-full h-1 bg-slate-200 -z-10 -translate-y-1/2"></div>
            <div className="absolute top-1/2 left-0 h-1 bg-blue-600 -z-10 -translate-y-1/2 transition-all duration-300" style={{ width: `${((currentStep - 1) / 6) * 100}%` }}></div>
            
            {STEPS.map((step) => {
              const Icon = step.icon;
              const isActive = step.id === currentStep;
              const isCompleted = step.id < currentStep;
              return (
                <div key={step.id} className="flex flex-col items-center">
                  <div className={`h-10 w-10 rounded-full flex items-center justify-center border-2 transition-colors ${
                    isActive ? 'border-blue-600 bg-white text-blue-600 shadow-md' : 
                    isCompleted ? 'border-blue-600 bg-blue-600 text-white' : 
                    'border-slate-300 bg-slate-100 text-slate-400'
                  }`}>
                    {isCompleted ? <CheckCircle2 className="h-5 w-5" /> : <Icon className="h-5 w-5" />}
                  </div>
                  <span className={`text-xs mt-2 font-medium hidden sm:block ${isActive ? 'text-blue-600' : 'text-slate-500'}`}>{step.name}</span>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 max-w-2xl w-full mx-auto p-4 sm:p-6 mt-8">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="p-8">
            
            {currentStep === 1 && (
              <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
                <h2 className="text-2xl font-bold text-slate-900 text-center mb-8">Información de la Empresa</h2>
                <div>
                  <label className="block text-sm font-medium text-slate-700">Razón Social</label>
                  <input type="text" className="mt-1 block w-full h-12 rounded-md border-slate-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-lg px-4" placeholder="Ej: Mi Empresa S.A." value={companyData.name} onChange={e => setCompanyData({...companyData, name: e.target.value})} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700">RUC</label>
                  <input type="text" className="mt-1 block w-full h-12 rounded-md border-slate-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-lg px-4" placeholder="Ej: 155555555-2-2000" value={companyData.ruc} onChange={e => setCompanyData({...companyData, ruc: e.target.value})} />
                </div>
              </div>
            )}

            {currentStep === 2 && (
              <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
                <div className="text-center mb-8">
                  <h2 className="text-2xl font-bold text-slate-900">Sucursales</h2>
                  <p className="text-slate-500 mt-2">¿Dónde operan tus puntos de venta?</p>
                </div>
                {branches.map((b, i) => (
                  <div key={i} className="flex gap-2">
                    <input type="text" className="flex-1 h-10 rounded-md border-slate-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 px-3" placeholder="Nombre de sucursal" value={b.name} onChange={e => {
                      const nb = [...branches]; nb[i].name = e.target.value; setBranches(nb);
                    }} />
                  </div>
                ))}
                <button type="button" onClick={() => setBranches([...branches, {name: ''}])} className="text-blue-600 text-sm font-medium hover:text-blue-800">+ Añadir otra sucursal</button>
              </div>
            )}

            {currentStep === 3 && (
              <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
                <div className="text-center mb-8">
                  <h2 className="text-2xl font-bold text-slate-900">Cuentas Bancarias</h2>
                  <p className="text-slate-500 mt-2">Agrega las cuentas donde depositas tu efectivo.</p>
                </div>
                {bankAccounts.map((b, i) => (
                  <div key={i} className="flex gap-2 mb-4">
                    <input type="text" className="w-1/2 h-10 rounded-md border-slate-300 shadow-sm focus:border-blue-500 px-3" placeholder="Banco (Ej: Banco General)" value={b.name} onChange={e => {
                      const nb = [...bankAccounts]; nb[i].name = e.target.value; setBankAccounts(nb);
                    }} />
                    <input type="text" className="w-1/2 h-10 rounded-md border-slate-300 shadow-sm focus:border-blue-500 px-3" placeholder="Nro de Cuenta" value={b.account_number} onChange={e => {
                      const nb = [...bankAccounts]; nb[i].account_number = e.target.value; setBankAccounts(nb);
                    }} />
                  </div>
                ))}
                <button type="button" onClick={() => setBankAccounts([...bankAccounts, {name: '', account_number: ''}])} className="text-blue-600 text-sm font-medium hover:text-blue-800">+ Añadir otra cuenta</button>
              </div>
            )}

            {currentStep === 4 && (
              <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
                <div className="text-center mb-8">
                  <h2 className="text-2xl font-bold text-slate-900">Formas de Pago</h2>
                  <p className="text-slate-500 mt-2">¿Cómo te pagan tus clientes? Asócialo a una cuenta bancaria.</p>
                </div>
                {paymentMethods.map((p, i) => (
                  <div key={i} className="flex gap-2 mb-4">
                    <input type="text" className="w-1/2 h-10 rounded-md border-slate-300 shadow-sm focus:border-blue-500 px-3" placeholder="Forma de pago (Ej: Visa)" value={p.name} onChange={e => {
                      const np = [...paymentMethods]; np[i].name = e.target.value; setPaymentMethods(np);
                    }} />
                    <select className="w-1/2 h-10 rounded-md border-slate-300 shadow-sm focus:border-blue-500 px-3" value={p.bank_account_id} onChange={e => {
                      const np = [...paymentMethods]; np[i].bank_account_id = e.target.value; setPaymentMethods(np);
                    }}>
                      <option value="" disabled>Cuenta Destino...</option>
                      {bankAccounts.filter(b => b.id).map(b => (
                        <option key={b.id} value={b.id}>{b.name}</option>
                      ))}
                    </select>
                  </div>
                ))}
                <button type="button" onClick={() => setPaymentMethods([...paymentMethods, {name: '', bank_account_id: ''}])} className="text-blue-600 text-sm font-medium hover:text-blue-800">+ Añadir otra forma de pago</button>
              </div>
            )}

            {currentStep === 5 && (
              <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
                <div className="text-center mb-8">
                  <h2 className="text-2xl font-bold text-slate-900">Invitar Usuarios</h2>
                  <p className="text-slate-500 mt-2">¿Quiénes registrarán los cierres?</p>
                  <p className="text-blue-600 text-sm mt-1 font-medium bg-blue-50 py-1 px-3 rounded-full inline-block">
                    Le llegará un correo a la persona que asignes para que cree su contraseña y se registre.
                  </p>
                </div>
                {users.map((u, i) => (
                  <div key={i} className="mb-6 p-4 border border-slate-200 rounded-lg bg-slate-50 shadow-sm">
                    <div className="flex gap-2 mb-2">
                      <input type="email" className="w-2/3 h-10 rounded-md border-slate-300 shadow-sm focus:border-blue-500 px-3" placeholder="Correo electrónico" value={u.email} onChange={e => {
                        const nu = [...users]; nu[i].email = e.target.value; setUsers(nu);
                      }} />
                      <select className="w-1/3 h-10 rounded-md border-slate-300 shadow-sm focus:border-blue-500 px-3" value={u.role} onChange={e => {
                        const nu = [...users]; nu[i].role = e.target.value; setUsers(nu);
                      }}>
                        <option value="user">Cajero</option>
                        <option value="admin">Administrador</option>
                      </select>
                    </div>
                    {u.role === 'user' && (
                      <div className="mt-3">
                        <label className="block text-xs font-medium text-slate-500 mb-2">Asignar a Sucursales:</label>
                        <div className="flex flex-wrap gap-2">
                          {branches.filter(b => b.id).map(b => (
                            <label key={b.id} className={`inline-flex items-center border rounded px-2 py-1 cursor-pointer transition-colors ${u.branch_ids.includes(b.id!) ? 'bg-blue-50 border-blue-200' : 'bg-white border-slate-200 hover:bg-slate-100'}`}>
                              <input type="checkbox" className="rounded text-blue-600 focus:ring-blue-500 h-3 w-3 mr-1.5" checked={u.branch_ids.includes(b.id!)} onChange={e => {
                                const nu = [...users];
                                if (e.target.checked) {
                                  nu[i].branch_ids.push(b.id!);
                                } else {
                                  nu[i].branch_ids = nu[i].branch_ids.filter(id => id !== b.id);
                                }
                                setUsers(nu);
                              }} />
                              <span className={`text-xs font-medium ${u.branch_ids.includes(b.id!) ? 'text-blue-700' : 'text-slate-600'}`}>{b.name}</span>
                            </label>
                          ))}
                          {branches.filter(b => b.id).length === 0 && (
                            <span className="text-xs text-amber-600">Aún no hay sucursales guardadas. Retrocede al Paso 2 para crearlas.</span>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
                <button type="button" onClick={() => setUsers([...users, {email: '', role: 'user', branch_ids: []}])} className="text-blue-600 text-sm font-medium hover:text-blue-800">+ Añadir otro usuario</button>
              </div>
            )}

            {currentStep === 6 && (
              <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
                <div className="text-center mb-8">
                  <h2 className="text-2xl font-bold text-slate-900">Secuencia de Cierres Z</h2>
                  <p className="text-slate-500 mt-2">¿Cómo prefieres que se maneje el número de Cierre Z?</p>
                </div>
                
                <div className="space-y-4">
                  <div className={`border-2 p-4 rounded-lg cursor-pointer transition-colors ${sequenceSettings.z_sequence_type === 'manual' ? 'border-blue-600 bg-blue-50' : 'border-slate-200 hover:border-blue-300'}`} onClick={() => setSequenceSettings({...sequenceSettings, z_sequence_type: 'manual'})}>
                    <div className="flex items-center">
                      <input type="radio" checked={sequenceSettings.z_sequence_type === 'manual'} readOnly className="h-4 w-4 text-blue-600" />
                      <label className="ml-3 font-medium text-slate-900">Manual (Recomendado para inicio)</label>
                    </div>
                    <p className="ml-7 mt-1 text-sm text-slate-500">El cajero deberá escribir el número impreso en el ticket de la caja registradora en cada cierre.</p>
                  </div>

                  <div className={`border-2 p-4 rounded-lg cursor-pointer transition-colors ${sequenceSettings.z_sequence_type === 'auto' ? 'border-blue-600 bg-blue-50' : 'border-slate-200 hover:border-blue-300'}`} onClick={() => setSequenceSettings({...sequenceSettings, z_sequence_type: 'auto'})}>
                    <div className="flex items-center">
                      <input type="radio" checked={sequenceSettings.z_sequence_type === 'auto'} readOnly className="h-4 w-4 text-blue-600" />
                      <label className="ml-3 font-medium text-slate-900">Automático (Correlativo interno)</label>
                    </div>
                    <p className="ml-7 mt-1 text-sm text-slate-500">El sistema asignará el número de forma automática. El cajero no podrá modificarlo.</p>
                    
                    {sequenceSettings.z_sequence_type === 'auto' && (
                      <div className="ml-7 mt-4">
                        <label className="block text-sm font-medium text-slate-700">¿Con qué número iniciamos?</label>
                        <input type="number" className="mt-1 block w-32 h-10 rounded-md border-slate-300 shadow-sm focus:border-blue-500 px-3" value={sequenceSettings.z_current_sequence} onChange={e => setSequenceSettings({...sequenceSettings, z_current_sequence: parseInt(e.target.value) || 0})} />
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {currentStep === 7 && (
              <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300 text-center">
                <div className="w-20 h-20 bg-gradient-to-r from-purple-500 to-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg rotate-3">
                  <BrainCircuit className="h-10 w-10 text-white" />
                </div>
                <h2 className="text-3xl font-bold text-slate-900">Validador de IA (Opcional)</h2>
                <p className="text-slate-600 text-lg max-w-md mx-auto">
                  ¿Deseas activar el trabajador de Inteligencia Artificial para que extraiga automáticamente los datos de los tickets Z subidos?
                </p>
                
                <div className="mt-8 flex justify-center space-x-6">
                  <button onClick={() => setUseAI(false)} className={`px-6 py-3 rounded-lg border-2 font-medium transition-colors ${!useAI ? 'border-slate-800 bg-slate-800 text-white shadow-md' : 'border-slate-300 text-slate-700 hover:bg-slate-50'}`}>
                    No, llenado manual
                  </button>
                  <button onClick={() => setUseAI(true)} className={`px-6 py-3 rounded-lg border-2 font-medium transition-colors flex items-center ${useAI ? 'border-purple-600 bg-purple-600 text-white shadow-md' : 'border-purple-200 text-purple-700 hover:bg-purple-50'}`}>
                    Sí, activar IA <span className="ml-2 bg-purple-500 text-white text-xs px-2 py-0.5 rounded-full">BETA</span>
                  </button>
                </div>
              </div>
            )}

          </div>
          
          {/* Footer Navigation */}
          <div className="bg-slate-50 px-8 py-4 border-t border-slate-200 flex items-center justify-between">
            <button
              onClick={handleBack}
              disabled={currentStep === 1 || loading}
              className={`flex items-center px-4 py-2 text-sm font-medium text-slate-700 hover:text-slate-900 ${currentStep === 1 ? 'invisible' : ''}`}
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Atrás
            </button>
            <button
              onClick={handleNext}
              disabled={loading}
              className="flex items-center px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg shadow-sm transition-colors disabled:opacity-50"
            >
              {loading ? 'Procesando...' : currentStep === 7 ? 'Finalizar Configuración' : 'Siguiente'}
              {!loading && currentStep < 7 && <ArrowRight className="ml-2 h-4 w-4" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Onboarding;

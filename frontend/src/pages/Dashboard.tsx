import React, { useState, useEffect } from 'react';
import { LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, AlertTriangle, Store, DollarSign } from 'lucide-react';
import api from '../services/api';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

const Dashboard: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const userStr = localStorage.getItem('user');
        const user = userStr ? JSON.parse(userStr) : {};
        const activeCompanyIdStr = localStorage.getItem('active_company_id');
        const companyId = activeCompanyIdStr ? parseInt(activeCompanyIdStr) : user.company_id || 1;
        const res = await api.get(`/dashboard/metrics?company_id=${companyId}`);
        setData(res.data);
      } catch (err) {
        console.error("Error fetching dashboard metrics", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <div className="p-8 text-center text-slate-500">Cargando métricas...</div>;
  if (!data) return <div className="p-8 text-center text-red-500">Error cargando dashboard</div>;

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Panel Principal</h1>
        <p className="text-slate-500">Resumen operativo de hoy</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex items-center">
          <div className="p-3 rounded-full bg-blue-100 text-blue-600 mr-4">
            <DollarSign className="h-6 w-6" />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">Ventas de Hoy</p>
            <p className="text-2xl font-bold text-slate-900">${data.kpis.total_sales_today.toLocaleString('en-US', {minimumFractionDigits: 2})}</p>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex items-center">
          <div className={`p-3 rounded-full mr-4 ${data.kpis.total_difference_today !== 0 ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'}`}>
            <AlertTriangle className="h-6 w-6" />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">Descuadres Totales</p>
            <p className={`text-2xl font-bold ${data.kpis.total_difference_today !== 0 ? 'text-red-600' : 'text-green-600'}`}>
              ${Math.abs(data.kpis.total_difference_today).toLocaleString('en-US', {minimumFractionDigits: 2})}
            </p>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex items-center">
          <div className="p-3 rounded-full bg-indigo-100 text-indigo-600 mr-4">
            <Store className="h-6 w-6" />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">Cierres de Hoy</p>
            <p className="text-2xl font-bold text-slate-900">{data.kpis.closed_branches} / {data.kpis.total_branches}</p>
          </div>
        </div>
        
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex items-center">
          <div className="p-3 rounded-full bg-emerald-100 text-emerald-600 mr-4">
            <TrendingUp className="h-6 w-6" />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">Estado General</p>
            <p className="text-lg font-bold text-emerald-600">
              {data.kpis.closed_branches === data.kpis.total_branches ? 'Todo cerrado' : 'En proceso'}
            </p>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Tendencia Semanal */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 lg:col-span-2">
          <h2 className="text-lg font-bold text-slate-900 mb-4">Tendencia de Ventas (7 días)</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.weekly_trend}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="date" tickFormatter={(val) => val.split('-').slice(1).join('/')} />
                <YAxis />
                <Tooltip formatter={(value: any) => [`$${Number(value).toFixed(2)}`, 'Ventas']} />
                <Line type="monotone" dataKey="sales" stroke="#2563eb" strokeWidth={3} dot={{r: 4}} activeDot={{r: 8}} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Distribucion de Metodos de Pago */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h2 className="text-lg font-bold text-slate-900 mb-4">Pagos de Hoy</h2>
          <div className="h-72">
            {data.payment_distribution.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data.payment_distribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {data.payment_distribution.map((_entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: any) => [`$${Number(value).toFixed(2)}`, 'Monto']} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-400">Sin datos aún</div>
            )}
          </div>
        </div>
      </div>

      {/* Alertas */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="p-6 border-b border-slate-200">
          <h2 className="text-lg font-bold text-slate-900">Atención Requerida (Descuadres y Alertas de IA)</h2>
        </div>
        <div className="divide-y divide-slate-200">
          {data.alerts.length === 0 ? (
            <div className="p-6 text-center text-slate-500">No hay alertas críticas recientes.</div>
          ) : (
            data.alerts.map((alert: any) => (
              <div key={alert.id} className="p-6 flex items-start">
                <div className="p-2 rounded-full bg-amber-100 text-amber-600 mr-4 mt-1">
                  <AlertTriangle className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-md font-bold text-slate-900">{alert.branch_name} - Cierre {alert.z_number}</h3>
                  <div className="mt-1 flex space-x-4 text-sm">
                    {alert.difference_amount !== 0 && (
                      <span className="text-red-600 font-medium">Diferencia de ${Math.abs(alert.difference_amount).toFixed(2)}</span>
                    )}
                    {alert.ai_comments && (
                      <span className="text-amber-600">Alerta de IA: {alert.ai_comments}</span>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

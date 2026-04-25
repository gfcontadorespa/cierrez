import React from 'react';

const Dashboard: React.FC = () => {
  return (
    <div>
      <div className="md:flex md:items-center md:justify-between mb-6">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-slate-900 sm:text-3xl sm:truncate">
            Panel Principal
          </h2>
        </div>
      </div>
      
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium leading-6 text-slate-900">
          Bienvenido al nuevo sistema SaaS
        </h3>
        <p className="mt-2 text-sm text-slate-500">
          Desde aquí podrás monitorear tus sucursales y la actividad de los cierres Z procesados por inteligencia artificial.
        </p>
      </div>
    </div>
  );
};

export default Dashboard;

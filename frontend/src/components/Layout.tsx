import React from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';
import { LayoutDashboard, Wallet, Receipt, LogOut, Building2, Users, Landmark, Store } from 'lucide-react';

const Layout: React.FC = () => {
  const location = useLocation();
  const user = JSON.parse(localStorage.getItem('user') || '{}');

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Cierres Z', href: '/cierres', icon: Receipt },
  ];

  const companySettingsNavigation = [
    { name: 'General / Logo', href: '/settings/general', icon: Building2 },
    { name: 'Mi Equipo', href: '/settings/team', icon: Users },
    { name: 'Cuentas Bancarias', href: '/settings/bank-accounts', icon: Landmark },
    { name: 'Formas de Pago', href: '/settings/payment-methods', icon: Wallet },
    { name: 'Sucursales', href: '/settings/branches', icon: Store },
  ];

  const adminNavigation = [
    { name: 'Compañías', href: '/admin/companies', icon: Building2 },
    { name: 'Usuarios', href: '/admin/users', icon: Users },
  ];

  const classNames = (...classes: string[]) => {
    return classes.filter(Boolean).join(' ');
  };

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Sidebar */}
      <div className="flex flex-col w-64 bg-slate-900 border-r border-slate-800">
        <div className="flex items-center justify-center h-16 bg-slate-900 px-4 sm:px-6 lg:px-8 border-b border-slate-800">
          <span className="text-white text-xl font-bold">Validador SaaS</span>
        </div>
        <div className="flex-1 flex flex-col overflow-y-auto">
          <nav className="flex-1 px-2 py-4 space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname.startsWith(item.href) && item.href !== '#';
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={classNames(
                    isActive ? 'bg-slate-800 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white',
                    'group flex items-center px-2 py-2 text-sm font-medium rounded-md'
                  )}
                >
                  <item.icon
                    className={classNames(
                      isActive ? 'text-white' : 'text-slate-400 group-hover:text-white',
                      'mr-3 flex-shrink-0 h-6 w-6'
                    )}
                    aria-hidden="true"
                  />
                  {item.name}
                </Link>
              );
            })}
          </nav>

          {/* Sección Configuración de la Compañía */}
          {(user?.role === 'admin' || user?.is_global_admin) && (
            <div className="mt-6">
              <h3 className="px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider" id="company-settings-headline">
                Configuración
              </h3>
              <nav className="mt-2 px-2 space-y-1" aria-labelledby="company-settings-headline">
                {companySettingsNavigation.map((item) => {
                  const isActive = location.pathname.startsWith(item.href) && item.href !== '#';
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      className={classNames(
                        isActive ? 'bg-slate-800 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white',
                        'group flex items-center px-2 py-2 text-sm font-medium rounded-md'
                      )}
                    >
                      <item.icon
                        className={classNames(
                          isActive ? 'text-white' : 'text-slate-400 group-hover:text-white',
                          'mr-3 flex-shrink-0 h-6 w-6'
                        )}
                        aria-hidden="true"
                      />
                      {item.name}
                    </Link>
                  );
                })}
              </nav>
            </div>
          )}

          {/* Sección Admin Global */}
          {user?.is_global_admin && (
            <div className="mt-8">
              <h3 className="px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider" id="admin-headline">
                Administración Global
              </h3>
              <nav className="mt-2 px-2 space-y-1" aria-labelledby="admin-headline">
                {adminNavigation.map((item) => {
                  const isActive = location.pathname.startsWith(item.href) && item.href !== '#';
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      className={classNames(
                        isActive ? 'bg-slate-800 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white',
                        'group flex items-center px-2 py-2 text-sm font-medium rounded-md'
                      )}
                    >
                      <item.icon
                        className={classNames(
                          isActive ? 'text-white' : 'text-slate-400 group-hover:text-white',
                          'mr-3 flex-shrink-0 h-6 w-6'
                        )}
                        aria-hidden="true"
                      />
                      {item.name}
                    </Link>
                  );
                })}
              </nav>
            </div>
          )}
        </div>
        <div className="flex-shrink-0 flex border-t border-slate-800 p-4">
          <Link to="/" className="flex-shrink-0 group block w-full">
            <div className="flex items-center text-slate-300 hover:text-white transition-colors">
              <LogOut className="inline-block h-5 w-5 mr-2" />
              <div className="text-sm font-medium">Cerrar Sesión</div>
            </div>
          </Link>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col">
        {/* Top Navbar */}
        <div className="sticky top-0 z-10 flex-shrink-0 h-16 bg-white border-b border-slate-200 flex items-center justify-between px-4 sm:px-6 lg:px-8">
            <div className="flex-1"></div>
            <div className="ml-4 flex items-center md:ml-6">
              <div className="flex items-center">
                <span className="text-sm font-medium text-slate-700 mr-2">{user?.name || user?.email || 'Usuario'}</span>
                <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-bold uppercase">
                  {(user?.name || user?.email || 'U').charAt(0)}
                </div>
              </div>
            </div>
        </div>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;

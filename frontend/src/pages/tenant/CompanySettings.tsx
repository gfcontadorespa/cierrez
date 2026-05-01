import React, { useState, useEffect } from 'react';
import { Upload, Save, Building2 } from 'lucide-react';

export default function CompanySettings() {
  const [logoUrl, setLogoUrl] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const companyId = user.company_id;

  useEffect(() => {
    if (companyId) {
      fetchCompanies();
    }
  }, [companyId]);

  const fetchCompanies = async () => {
    try {
      const response = await fetch('/api/companies');
      if (response.ok) {
        const companies = await response.json();
        const myCompany = companies.find((c: any) => c.id === companyId);
        if (myCompany && myCompany.logo_url) {
          setLogoUrl(myCompany.logo_url);
        }
      }
    } catch (error) {
      console.error('Error fetching companies:', error);
    }
  };

  const handleLogoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/upload/logo', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Error al subir el logo');
      
      const data = await response.json();
      setLogoUrl(data.url);
      setMessage('Imagen subida correctamente. No olvides guardar los cambios.');
    } catch (error) {
      console.error('Upload error:', error);
      setMessage('Error al subir la imagen.');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!companyId) return;
    
    setSaving(true);
    try {
      const response = await fetch(`/api/companies/${companyId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ logo_url: logoUrl }),
      });

      if (!response.ok) throw new Error('Error al guardar configuración');
      
      setMessage('Configuración guardada exitosamente.');
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      console.error('Save error:', error);
      setMessage('Error al guardar la configuración.');
    } finally {
      setSaving(false);
    }
  };

  if (!companyId) {
    return <div className="p-4 text-center">No perteneces a una compañía configurada.</div>;
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Configuración de Empresa</h1>
        <p className="text-sm text-slate-500">Administra los detalles y la marca de tu empresa.</p>
      </div>

      <div className="bg-white rounded-lg shadow p-6 max-w-2xl">
        <h2 className="text-lg font-medium text-slate-900 mb-4 flex items-center">
          <Building2 className="w-5 h-5 mr-2 text-slate-500" />
          Logo Corporativo
        </h2>
        
        <p className="text-sm text-slate-500 mb-4">
          Este logo aparecerá en la cabecera de los Reportes de Cierre Z en PDF.
        </p>

        <div className="flex items-start space-x-6">
          <div className="flex-shrink-0">
            {logoUrl ? (
              <img src={logoUrl} alt="Logo" className="h-32 w-auto object-contain border rounded p-2" />
            ) : (
              <div className="h-32 w-32 bg-slate-100 flex items-center justify-center border rounded text-slate-400">
                Sin logo
              </div>
            )}
          </div>
          
          <div className="flex-1">
            <div className="flex items-center justify-center w-full">
              <label htmlFor="dropzone-file" className="flex flex-col items-center justify-center w-full h-32 border-2 border-slate-300 border-dashed rounded-lg cursor-pointer bg-slate-50 hover:bg-slate-100">
                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                  <Upload className="w-8 h-8 mb-2 text-slate-500" />
                  <p className="mb-2 text-sm text-slate-500"><span className="font-semibold">Click para subir</span> o arrastra y suelta</p>
                  <p className="text-xs text-slate-500">PNG, JPG, JPEG (Max. 2MB)</p>
                </div>
                <input id="dropzone-file" type="file" className="hidden" accept="image/png, image/jpeg" onChange={handleLogoUpload} disabled={loading} />
              </label>
            </div>
            {loading && <p className="text-sm text-blue-500 mt-2">Subiendo imagen...</p>}
          </div>
        </div>

        {message && (
          <div className={`mt-4 p-3 rounded text-sm ${message.includes('Error') ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'}`}>
            {message}
          </div>
        )}

        <div className="mt-6 flex justify-end">
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            <Save className="w-4 h-4 mr-2" />
            {saving ? 'Guardando...' : 'Guardar Cambios'}
          </button>
        </div>
      </div>
    </div>
  );
}

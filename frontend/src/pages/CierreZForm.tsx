import React, { useState, useEffect, useRef } from 'react';
import { ArrowLeft, Save, Plus, Trash2, Calculator, UploadCloud, X } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api';

interface PaymentMethod {
  id: number;
  name: string;
}

interface PaymentRow {
  payment_method_id: string;
  amount: string;
}

interface Branch {
  id: number;
  name: string;
}

const CierreZForm: React.FC = () => {
  const navigate = useNavigate();
  const zInputRef = useRef<HTMLInputElement>(null);
  const posInputRef = useRef<HTMLInputElement>(null);
  const depositInputRef = useRef<HTMLInputElement>(null);
  
  const [loading, setLoading] = useState(false);
  const [uploadingImage, setUploadingImage] = useState(false);
  
  const [zFile, setZFile] = useState<File | null>(null);
  const [zPreview, setZPreview] = useState<string | null>(null);
  
  const [posFile, setPosFile] = useState<File | null>(null);
  const [posPreview, setPosPreview] = useState<string | null>(null);
  
  const [depositFile, setDepositFile] = useState<File | null>(null);
  const [depositPreview, setDepositPreview] = useState<string | null>(null);

  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);
  
  // Master Header State
  const [header, setHeader] = useState({
    branch_id: '',
    z_number: '',
    date_closed: new Date().toISOString().split('T')[0],
    taxable_sales: '',
    exempt_sales: '',
    tax_amount: ''
  });

  // Details State
  const [payments, setPayments] = useState<PaymentRow[]>([
    { payment_method_id: '', amount: '' }
  ]);

  useEffect(() => {
    // Cargar formas de pago y sucursales
    const fetchDropdowns = async () => {
      try {
        const [pmRes, brRes] = await Promise.all([
          api.get('/payment_methods?company_id=1'),
          api.get('/branches?company_id=1')
        ]);
        setPaymentMethods(pmRes.data);
        setBranches(brRes.data);
        if (brRes.data.length > 0) {
          setHeader(prev => ({...prev, branch_id: brRes.data[0].id.toString()}));
        }
      } catch (error) {
        console.error('Error fetching dropdowns:', error);
      }
    };
    fetchDropdowns();
  }, []);

  // Calculados
  const parseNum = (val: string) => parseFloat(val) || 0;
  
  const totalSales = parseNum(header.taxable_sales) + parseNum(header.exempt_sales);
  const totalReceipt = totalSales + parseNum(header.tax_amount);
  
  const totalPayments = payments.reduce((acc, curr) => acc + parseNum(curr.amount), 0);
  const difference = totalReceipt - totalPayments;
  const isBalanced = Math.abs(difference) < 0.01;

  // Validación de Impuesto (Aproximado al 7%)
  const expectedTax = parseNum(header.taxable_sales) * 0.07;
  const actualTax = parseNum(header.tax_amount);
  const taxDifference = Math.abs(expectedTax - actualTax);
  const isTaxWarning = parseNum(header.taxable_sales) > 0 && taxDifference > 0.10; // Margen de error de 10 centavos por redondeos

  const handleAddRow = () => {
    setPayments([...payments, { payment_method_id: '', amount: '' }]);
  };

  const handleRemoveRow = (index: number) => {
    const newPayments = [...payments];
    newPayments.splice(index, 1);
    setPayments(newPayments);
  };

  const handlePaymentChange = (index: number, field: keyof PaymentRow, value: string) => {
    const newPayments = [...payments];
    newPayments[index][field] = value;
    setPayments(newPayments);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>, type: 'z' | 'pos' | 'deposit') => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const preview = URL.createObjectURL(file);
      if (type === 'z') { setZFile(file); setZPreview(preview); }
      if (type === 'pos') { setPosFile(file); setPosPreview(preview); }
      if (type === 'deposit') { setDepositFile(file); setDepositPreview(preview); }
    }
  };

  const removeFile = (type: 'z' | 'pos' | 'deposit') => {
    if (type === 'z') { setZFile(null); setZPreview(null); if (zInputRef.current) zInputRef.current.value = ''; }
    if (type === 'pos') { setPosFile(null); setPosPreview(null); if (posInputRef.current) posInputRef.current.value = ''; }
    if (type === 'deposit') { setDepositFile(null); setDepositPreview(null); if (depositInputRef.current) depositInputRef.current.value = ''; }
  };

  const uploadFile = async (file: File | null) => {
    if (!file) return null;
    const formData = new FormData();
    formData.append('file', file);
    const baseUrl = import.meta.env.VITE_API_URL || '/api';
    const uploadRes = await fetch(`${baseUrl}/upload/receipt`, {
      method: 'POST',
      body: formData
    });
    if (!uploadRes.ok) throw new Error('Upload failed');
    const data = await uploadRes.json();
    return data.url;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!isBalanced) {
      if(!window.confirm(`Hay una diferencia de $${difference.toFixed(2)}. ¿Deseas guardarlo con descuadre?`)) {
        return;
      }
    }

    // Filtrar pagos vacíos
    const validPayments = payments.filter(p => p.payment_method_id && parseNum(p.amount) > 0).map(p => ({
      payment_method_id: parseInt(p.payment_method_id),
      amount: parseNum(p.amount)
    }));

    try {
      setLoading(true);

      // 1. Subir imágenes en paralelo
      setUploadingImage(true);
      const [zUrl, posUrl, depositUrl] = await Promise.all([
        uploadFile(zFile),
        uploadFile(posFile),
        uploadFile(depositFile)
      ]);
      setUploadingImage(false);

      const payload = {
        company_id: 1, // Provisional
        branch_id: header.branch_id ? parseInt(header.branch_id) : 1,
        z_number: header.z_number,
        date_closed: header.date_closed,
        taxable_sales: parseNum(header.taxable_sales),
        exempt_sales: parseNum(header.exempt_sales),
        tax_amount: parseNum(header.tax_amount),
        total_sales: totalSales,
        total_receipt: totalReceipt,
        difference_amount: difference,
        image_url: zUrl,
        pos_receipt_url: posUrl,
        deposit_receipt_url: depositUrl,
        payments: validPayments
      };

      await api.post('/cierres', payload);
      navigate('/cierres');
    } catch (error) {
      console.error('Error saving cierre:', error);
      alert('Error al guardar el Cierre Z o subir la imagen');
    } finally {
      setLoading(false);
      setUploadingImage(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center">
          <Link to="/cierres" className="mr-4 text-slate-400 hover:text-slate-600">
            <ArrowLeft className="h-6 w-6" />
          </Link>
          <h2 className="text-2xl font-bold leading-7 text-slate-900">Registrar Cierre Z</h2>
        </div>
        <button
          onClick={handleSubmit}
          disabled={loading || uploadingImage}
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
        >
          <Save className="mr-2 h-4 w-4" />
          {uploadingImage ? 'Subiendo...' : 'Guardar Cierre'}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Columna Izquierda: Datos Maestros */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-slate-900 mb-4 border-b pb-2">1. Datos del Cierre</h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700">Sucursal</label>
                <select required className="mt-1 block w-full h-10 border border-slate-300 bg-white rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm" value={header.branch_id} onChange={e => setHeader({...header, branch_id: e.target.value})}>
                  <option value="" disabled>Seleccione...</option>
                  {branches.map(b => (
                    <option key={b.id} value={b.id}>{b.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700">Número de Cierre Z</label>
                <input type="text" required className="mt-1 block w-full h-10 border border-slate-300 rounded-md shadow-sm py-2 px-3 focus:ring-blue-500 focus:border-blue-500 sm:text-sm font-mono" value={header.z_number} onChange={e => setHeader({...header, z_number: e.target.value})} placeholder="Ej: Z-1024" />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700">Fecha</label>
                <input type="date" required className="mt-1 block w-full h-10 border border-slate-300 rounded-md shadow-sm py-2 px-3 focus:ring-blue-500 focus:border-blue-500 sm:text-sm" value={header.date_closed} onChange={e => setHeader({...header, date_closed: e.target.value})} />
              </div>
            </div>

            <h3 className="text-lg font-medium text-slate-900 mt-8 mb-4 border-b pb-2">2. Desglose de Ventas e Impuestos</h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700">Ventas Gravables ($)</label>
                <input type="number" step="0.01" min="0" className="mt-1 block w-full h-10 border border-slate-300 rounded-md shadow-sm py-2 px-3 focus:ring-blue-500 focus:border-blue-500 sm:text-sm text-right font-mono" value={header.taxable_sales} onChange={e => setHeader({...header, taxable_sales: e.target.value})} placeholder="0.00" />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700">Ventas Exentas ($)</label>
                <input type="number" step="0.01" min="0" className="mt-1 block w-full h-10 border border-slate-300 rounded-md shadow-sm py-2 px-3 focus:ring-blue-500 focus:border-blue-500 sm:text-sm text-right font-mono" value={header.exempt_sales} onChange={e => setHeader({...header, exempt_sales: e.target.value})} placeholder="0.00" />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700">Impuesto Calculado ($)</label>
                <input type="number" step="0.01" min="0" className={`mt-1 block w-full h-10 border rounded-md shadow-sm py-2 px-3 focus:outline-none sm:text-sm text-right font-mono ${isTaxWarning ? 'border-amber-400 bg-amber-50 focus:ring-amber-500 focus:border-amber-500 text-amber-900' : 'border-slate-300 bg-blue-50 focus:ring-blue-500 focus:border-blue-500'}`} value={header.tax_amount} onChange={e => setHeader({...header, tax_amount: e.target.value})} placeholder="0.00" />
                {isTaxWarning && (
                  <p className="mt-1 text-xs text-amber-600">
                    ⚠️ El 7% esperado es aprox. ${expectedTax.toFixed(2)}
                  </p>
                )}
              </div>
            </div>
          </div>

          <div className="bg-white shadow rounded-lg p-6">
            <div className="flex justify-between items-center mb-4 border-b pb-2">
              <h3 className="text-lg font-medium text-slate-900">3. Formas de Pago</h3>
              <button type="button" onClick={handleAddRow} className="inline-flex items-center text-sm font-medium text-blue-600 hover:text-blue-500">
                <Plus className="mr-1 h-4 w-4" /> Añadir Fila
              </button>
            </div>
            
            <div className="space-y-3">
              {payments.map((payment, index) => (
                <div key={index} className="flex items-center space-x-3">
                  <div className="flex-1">
                    <select
                      className="block w-full h-10 bg-white border border-slate-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      value={payment.payment_method_id}
                      onChange={(e) => handlePaymentChange(index, 'payment_method_id', e.target.value)}
                    >
                      <option value="" disabled>Seleccione método...</option>
                      {paymentMethods.map(pm => (
                        <option key={pm.id} value={pm.id}>{pm.name}</option>
                      ))}
                    </select>
                  </div>
                  <div className="w-1/3">
                    <div className="relative rounded-md shadow-sm">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <span className="text-slate-500 sm:text-sm">$</span>
                      </div>
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        className="block w-full h-10 pl-7 pr-3 py-2 border border-slate-300 rounded-md focus:ring-blue-500 focus:border-blue-500 sm:text-sm text-right font-mono"
                        placeholder="0.00"
                        value={payment.amount}
                        onChange={(e) => handlePaymentChange(index, 'amount', e.target.value)}
                      />
                    </div>
                  </div>
                  <div className="w-10 flex justify-center">
                    {payments.length > 1 && (
                      <button type="button" onClick={() => handleRemoveRow(index)} className="text-red-400 hover:text-red-600">
                        <Trash2 className="h-5 w-5" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-slate-900 mb-4 border-b pb-2">4. Soportes (Imágenes)</h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {/* Cierre Z */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">1. Cierre Z</label>
                {!zPreview ? (
                  <div className="flex justify-center px-4 py-4 border-2 border-slate-300 border-dashed rounded-md hover:border-blue-500 hover:bg-slate-50 cursor-pointer" onClick={() => zInputRef.current?.click()}>
                    <div className="text-center">
                      <UploadCloud className="mx-auto h-8 w-8 text-slate-400" />
                      <span className="mt-2 block text-xs font-medium text-blue-600">Subir Z</span>
                      <input type="file" className="sr-only" ref={zInputRef} onChange={e => handleFileChange(e, 'z')} accept="image/*" />
                    </div>
                  </div>
                ) : (
                  <div className="relative border border-slate-200 rounded-md bg-slate-50 p-2 text-center h-32 flex items-center justify-center">
                    <button type="button" onClick={() => removeFile('z')} className="absolute top-1 right-1 p-1 bg-red-100 text-red-600 rounded-full hover:bg-red-200"><X className="h-4 w-4" /></button>
                    <img src={zPreview} className="max-h-full object-contain" />
                  </div>
                )}
              </div>
              
              {/* POS */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">2. Lote POS (Visa/Clave)</label>
                {!posPreview ? (
                  <div className="flex justify-center px-4 py-4 border-2 border-slate-300 border-dashed rounded-md hover:border-blue-500 hover:bg-slate-50 cursor-pointer" onClick={() => posInputRef.current?.click()}>
                    <div className="text-center">
                      <UploadCloud className="mx-auto h-8 w-8 text-slate-400" />
                      <span className="mt-2 block text-xs font-medium text-blue-600">Subir POS</span>
                      <input type="file" className="sr-only" ref={posInputRef} onChange={e => handleFileChange(e, 'pos')} accept="image/*" />
                    </div>
                  </div>
                ) : (
                  <div className="relative border border-slate-200 rounded-md bg-slate-50 p-2 text-center h-32 flex items-center justify-center">
                    <button type="button" onClick={() => removeFile('pos')} className="absolute top-1 right-1 p-1 bg-red-100 text-red-600 rounded-full hover:bg-red-200"><X className="h-4 w-4" /></button>
                    <img src={posPreview} className="max-h-full object-contain" />
                  </div>
                )}
              </div>

              {/* Deposit */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">3. Depósito Bancario</label>
                {!depositPreview ? (
                  <div className="flex justify-center px-4 py-4 border-2 border-slate-300 border-dashed rounded-md hover:border-blue-500 hover:bg-slate-50 cursor-pointer" onClick={() => depositInputRef.current?.click()}>
                    <div className="text-center">
                      <UploadCloud className="mx-auto h-8 w-8 text-slate-400" />
                      <span className="mt-2 block text-xs font-medium text-blue-600">Subir Depósito</span>
                      <input type="file" className="sr-only" ref={depositInputRef} onChange={e => handleFileChange(e, 'deposit')} accept="image/*" />
                    </div>
                  </div>
                ) : (
                  <div className="relative border border-slate-200 rounded-md bg-slate-50 p-2 text-center h-32 flex items-center justify-center">
                    <button type="button" onClick={() => removeFile('deposit')} className="absolute top-1 right-1 p-1 bg-red-100 text-red-600 rounded-full hover:bg-red-200"><X className="h-4 w-4" /></button>
                    <img src={depositPreview} className="max-h-full object-contain" />
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Columna Derecha: Resumen Matemático */}
        <div className="lg:col-span-1">
          <div className="bg-slate-800 rounded-lg shadow sticky top-6 overflow-hidden">
            <div className="p-4 bg-slate-900 border-b border-slate-700 flex items-center">
              <Calculator className="h-5 w-5 text-blue-400 mr-2" />
              <h3 className="text-lg font-medium text-white">Resumen del Cuadre</h3>
            </div>
            <div className="p-6 space-y-4 text-slate-300">
              <div className="flex justify-between items-center text-sm">
                <span>Ventas Totales:</span>
                <span className="font-mono">${totalSales.toFixed(2)}</span>
              </div>
              <div className="flex justify-between items-center text-sm">
                <span>Impuestos:</span>
                <span className="font-mono">${parseNum(header.tax_amount).toFixed(2)}</span>
              </div>
              <div className="pt-4 border-t border-slate-700 flex justify-between items-center text-lg font-bold text-white">
                <span>Total Cierre Z:</span>
                <span className="font-mono">${totalReceipt.toFixed(2)}</span>
              </div>

              <div className="mt-8 pt-8 border-t border-slate-700 flex justify-between items-center text-sm">
                <span>Total Pagado:</span>
                <span className="font-mono text-blue-400">${totalPayments.toFixed(2)}</span>
              </div>
              
              <div className={`mt-4 p-3 rounded-md flex justify-between items-center font-medium ${isBalanced ? 'bg-green-900/50 text-green-400 border border-green-800' : 'bg-red-900/50 text-red-400 border border-red-800'}`}>
                <span>Diferencia:</span>
                <span className="font-mono">${Math.abs(difference).toFixed(2)}</span>
              </div>
              {!isBalanced && (
                <p className="text-xs text-center text-slate-400 mt-2">
                  El total pagado debe ser igual al Total Cierre Z.
                </p>
              )}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

export default CierreZForm;

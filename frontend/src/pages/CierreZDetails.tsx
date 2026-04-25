import React, { useState, useEffect } from 'react';
import { ArrowLeft, Receipt, CheckCircle2, AlertTriangle, Printer } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import api from '../services/api';

interface PaymentDetail {
  id: number;
  payment_method_id: number;
  payment_method_name: string;
  amount: number;
}

interface CierreDetails {
  id: number;
  z_number: string;
  date_closed: string;
  taxable_sales: number;
  exempt_sales: number;
  tax_amount: number;
  total_sales: number;
  total_receipt: number;
  difference_amount: number;
  image_url: string | null;
  pos_receipt_url: string | null;
  deposit_receipt_url: string | null;
  status: string;
  payments: PaymentDetail[];
}

const CierreZDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [cierre, setCierre] = useState<CierreDetails | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCierre = async () => {
      try {
        setLoading(true);
        const response = await api.get(`/cierres/${id}`);
        setCierre(response.data);
      } catch (error) {
        console.error('Error fetching cierre details:', error);
      } finally {
        setLoading(false);
      }
    };
    if (id) fetchCierre();
  }, [id]);

  if (loading) return <div className="p-8 text-center text-slate-500">Cargando detalles del cierre...</div>;
  if (!cierre) return <div className="p-8 text-center text-red-500">Cierre no encontrado.</div>;

  const isBalanced = cierre.status === 'balanced';

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center">
          <Link to="/cierres" className="mr-4 text-slate-400 hover:text-slate-600">
            <ArrowLeft className="h-6 w-6" />
          </Link>
          <h2 className="text-2xl font-bold leading-7 text-slate-900">
            Detalle del Cierre <span className="text-slate-500 font-mono">{cierre.z_number}</span>
          </h2>
        </div>
        <button
          onClick={() => window.print()}
          className="inline-flex items-center px-4 py-2 border border-slate-300 rounded-md shadow-sm text-sm font-medium text-slate-700 bg-white hover:bg-slate-50"
        >
          <Printer className="mr-2 h-4 w-4 text-slate-500" /> Imprimir
        </button>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden border border-slate-200 print:shadow-none print:border-none">
        
        {/* Header Ribbon */}
        <div className={`px-6 py-4 flex items-center justify-between ${isBalanced ? 'bg-green-50 border-b border-green-100' : 'bg-red-50 border-b border-red-100'}`}>
          <div className="flex items-center">
            {isBalanced ? (
              <CheckCircle2 className="h-6 w-6 text-green-500 mr-2" />
            ) : (
              <AlertTriangle className="h-6 w-6 text-red-500 mr-2" />
            )}
            <span className={`font-medium ${isBalanced ? 'text-green-800' : 'text-red-800'}`}>
              {isBalanced ? 'Cierre Cuadrado Perfectamente' : `Cierre Descuadrado (Diferencia: $${Math.abs(cierre.difference_amount).toFixed(2)})`}
            </span>
          </div>
          <span className="text-sm font-medium text-slate-500">{cierre.date_closed}</span>
        </div>

        <div className="p-0 sm:p-0 flex flex-col lg:flex-row">
          
          {/* Columna Izquierda: Datos del Cierre */}
          <div className="flex-1 p-6 sm:p-8 border-r border-slate-200">
            <div className="flex items-center justify-between mb-8 pb-8 border-b border-slate-200">
              <div>
                <Receipt className="h-12 w-12 text-slate-300 mb-2" />
                <h1 className="text-2xl font-bold text-slate-900">Reporte Z</h1>
                <p className="text-slate-500">Documento de Cuadre de Caja</p>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-slate-500">N° Comprobante</p>
                <p className="text-xl font-mono font-bold text-slate-900">{cierre.z_number}</p>
              </div>
            </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8 pb-8 border-b border-slate-200">
            {/* Ventas */}
            <div>
              <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-4">Resumen de Ventas</h3>
              <dl className="space-y-3">
                <div className="flex justify-between">
                  <dt className="text-slate-500">Ventas Gravables</dt>
                  <dd className="font-mono text-slate-900">${cierre.taxable_sales.toFixed(2)}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-slate-500">Ventas Exentas</dt>
                  <dd className="font-mono text-slate-900">${cierre.exempt_sales.toFixed(2)}</dd>
                </div>
                <div className="flex justify-between border-t border-slate-100 pt-2">
                  <dt className="font-medium text-slate-900">Total Ventas</dt>
                  <dd className="font-mono font-medium text-slate-900">${cierre.total_sales.toFixed(2)}</dd>
                </div>
                <div className="flex justify-between text-blue-600">
                  <dt>Impuesto</dt>
                  <dd className="font-mono">${cierre.tax_amount.toFixed(2)}</dd>
                </div>
              </dl>
            </div>

            {/* Gran Total */}
            <div className="flex flex-col justify-center bg-slate-50 rounded-lg p-6 text-center">
              <span className="text-sm font-medium text-slate-500 mb-1">Gran Total del Cierre</span>
              <span className="text-4xl font-mono font-bold text-slate-900">${cierre.total_receipt.toFixed(2)}</span>
            </div>
          </div>

          {/* Pagos */}
          <div>
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-4">Desglose de Formas de Pago</h3>
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-slate-500 uppercase">Forma de Pago</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-slate-500 uppercase">Monto Declarado</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-slate-100">
                {cierre.payments.map((p) => (
                  <tr key={p.id}>
                    <td className="px-4 py-3 text-sm text-slate-900">{p.payment_method_name}</td>
                    <td className="px-4 py-3 text-sm font-mono text-right text-slate-900">${p.amount.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium text-slate-900">Total Pagado</th>
                  <th className="px-4 py-3 text-right text-sm font-mono font-bold text-slate-900 text-blue-600">
                    ${cierre.payments.reduce((acc, p) => acc + p.amount, 0).toFixed(2)}
                  </th>
                </tr>
                {!isBalanced && (
                  <tr className="bg-red-50">
                    <th className="px-4 py-3 text-left text-sm font-bold text-red-800">Diferencia</th>
                    <th className="px-4 py-3 text-right text-sm font-mono font-bold text-red-800">
                      ${Math.abs(cierre.difference_amount).toFixed(2)}
                    </th>
                  </tr>
                )}
              </tfoot>
            </table>
          </div>

        </div>

        {/* Columna Derecha: Imágenes de Soportes */}
          <div className="w-full lg:w-1/3 bg-slate-50 p-6 sm:p-8 flex flex-col space-y-6">
            
            {/* Cierre Z */}
            <div>
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-2 flex items-center">
                1. Cierre Z Original
              </h3>
              <div className="border-2 border-dashed border-slate-300 rounded-lg flex items-center justify-center bg-white overflow-hidden p-2 h-48">
                {cierre.image_url ? (
                  <a href={cierre.image_url} target="_blank" rel="noreferrer" title="Ver completo">
                    <img src={cierre.image_url} className="max-h-44 object-contain rounded hover:opacity-90 transition-opacity" />
                  </a>
                ) : (
                  <div className="text-center text-slate-400">
                    <Receipt className="h-8 w-8 mx-auto mb-1 opacity-50" />
                    <p className="text-xs">No adjunto</p>
                  </div>
                )}
              </div>
            </div>

            {/* Lote POS */}
            <div>
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-2 flex items-center">
                2. Lote POS (Tarjetas)
              </h3>
              <div className="border-2 border-dashed border-slate-300 rounded-lg flex items-center justify-center bg-white overflow-hidden p-2 h-48">
                {cierre.pos_receipt_url ? (
                  <a href={cierre.pos_receipt_url} target="_blank" rel="noreferrer" title="Ver completo">
                    <img src={cierre.pos_receipt_url} className="max-h-44 object-contain rounded hover:opacity-90 transition-opacity" />
                  </a>
                ) : (
                  <div className="text-center text-slate-400">
                    <Receipt className="h-8 w-8 mx-auto mb-1 opacity-50" />
                    <p className="text-xs">No adjunto</p>
                  </div>
                )}
              </div>
            </div>

            {/* Depósito */}
            <div>
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-2 flex items-center">
                3. Depósito Bancario
              </h3>
              <div className="border-2 border-dashed border-slate-300 rounded-lg flex items-center justify-center bg-white overflow-hidden p-2 h-48">
                {cierre.deposit_receipt_url ? (
                  <a href={cierre.deposit_receipt_url} target="_blank" rel="noreferrer" title="Ver completo">
                    <img src={cierre.deposit_receipt_url} className="max-h-44 object-contain rounded hover:opacity-90 transition-opacity" />
                  </a>
                ) : (
                  <div className="text-center text-slate-400">
                    <Receipt className="h-8 w-8 mx-auto mb-1 opacity-50" />
                    <p className="text-xs">No adjunto</p>
                  </div>
                )}
              </div>
            </div>

          </div>
          
        </div>
      </div>
    </div>
  );
};

export default CierreZDetails;

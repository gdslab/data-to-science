import { useMapContext } from '../MapContext';
import { FaCircleChevronRight } from 'react-icons/fa6';

import DataProductCard from './DataProductCard';
import { Flight } from '../../pages/workspace/projects/Project';
import LayerCard from './LayerCard';
import { LinkOutlineButton } from '../../Buttons';

import { formatDate } from './utils';

export default function FlightCard({ flight }: { flight: Flight }) {
  const { activeDataProduct } = useMapContext();

  return (
    <LayerCard>
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <strong
            className="font-bold text-slate-700 truncate flex-1 min-w-0"
            title={formatDate(flight.acquisition_date)}
          >
            {formatDate(flight.acquisition_date)}
          </strong>
          <div className="text-slate-600 text-xs font-medium whitespace-nowrap">
            {flight.sensor} · {flight.platform.replace('_', ' ')} ·{' '}
            {flight.altitude} m
          </div>
        </div>
        {flight.name && (
          <div
            className="text-sm text-slate-500 font-medium truncate"
            title={flight.name}
          >
            {flight.name}
          </div>
        )}
      </div>
      {flight.data_products.length > 0 && (
        <details
          className="mt-0.5 group [&_summary::-webkit-details-marker]:hidden overflow-visible"
          open={activeDataProduct?.flight_id === flight.id}
        >
          <summary className="text-sm cursor-pointer text-slate-600 hover:text-slate-800 hover:bg-slate-50 transition-colors flex items-center gap-1.5 px-2 py-1 -mx-2 rounded-sm focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-accent2 focus-visible:ring-offset-1">
            <FaCircleChevronRight
              className="h-4 w-4 transition-transform group-open:rotate-90"
              aria-hidden="true"
            />
            {flight.data_products.length} Data Product
            {flight.data_products.length !== 1 ? 's' : ''}
          </summary>
          <div className="mt-2 space-y-2">
            {flight.data_products.map((dataProduct) => (
              <DataProductCard key={dataProduct.id} dataProduct={dataProduct} />
            ))}
            <LinkOutlineButton
              size="sm"
              target="_blank"
              title="Open data management page for this flight in a new tab"
              url={`/projects/${flight.project_id}/flights/${flight.id}/data`}
            >
              Manage Data
            </LinkOutlineButton>
          </div>
        </details>
      )}
    </LayerCard>
  );
}

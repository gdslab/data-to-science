import { useMapContext } from '../MapContext';

import DataProductCard from './DataProductCard';
import { Flight } from '../../pages/projects/Project';
import LayerCard from './LayerCard';
import { LinkOutlineButton } from '../../Buttons';

import { formatDate } from './utils';

import UASIcon from '../../../assets/uas-icon.svg';

export default function FlightCard({ flight }: { flight: Flight }) {
  const { activeDataProduct } = useMapContext();

  return (
    <LayerCard>
      <div className="grid grid-cols-6">
        <div className="col-span-1 flex items-center justify-center">
          <img src={UASIcon} width={'50%'} />
        </div>
        <div className="col-span-5 flex flex-col items-start gap-2">
          <strong className="w-full font-bold text-slate-700 truncate">
            {formatDate(flight.acquisition_date)} {flight.name && `(${flight.name})`}
          </strong>
          <div className="grid grid-rows-2 text-slate-700 text-sm gap-1.5">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-sm text-gray-400 font-semibold">Platform: </span>
                {flight.platform.replace('_', ' ')}
              </div>
              <div>
                <span className="text-sm text-gray-400 font-semibold">Sensor:</span>{' '}
                {flight.sensor}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-sm text-gray-400 font-semibold">
                  Altitude (m):
                </span>{' '}
                {flight.altitude}
              </div>
            </div>
          </div>
        </div>
      </div>
      {flight.data_products.length > 0 && (
        <details
          className="group space-y-2 [&_summary::-webkit-details-marker]:hidden text-slate-600 overflow-visible"
          open={
            activeDataProduct && activeDataProduct.flight_id === flight.id
              ? true
              : false
          }
        >
          <summary className="text-sm cursor-pointer">{`${flight.data_products.length} Data Products`}</summary>
          {flight.data_products.map((dataProduct) => (
            <DataProductCard key={dataProduct.id} dataProduct={dataProduct} />
          ))}
          <div className="my-2">
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

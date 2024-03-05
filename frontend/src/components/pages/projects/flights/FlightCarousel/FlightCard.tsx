import { PhotoIcon } from '@heroicons/react/24/outline';

import { LinkButton, LinkOutlineButton } from '../../../../Buttons';
import Card from '../../../../Card';
import HintText from '../../../../HintText';
import { Flight } from '../../Project';

import { isGeoTIFF } from '../dataProducts/DataProductsTable';
import { useProjectContext } from '../../ProjectContext';
import FlightDeleteModal from '../FlightDeleteModal';

export default function FlightCard({ flight }: { flight: Flight }) {
  const { projectRole } = useProjectContext();

  const dataProduct = flight.data_products.length > 0 ? flight.data_products[0] : null;

  return (
    <div className="flex items-center justify-center min-h-96">
      <div className="w-80">
        <Card rounded={true}>
          <div className="grid grid-flow-row auto-rows-max gap-4">
            {/* preview image */}
            <div className="relative flex items-center justify-center bg-accent3/20">
              {dataProduct && isGeoTIFF(dataProduct.data_type) ? (
                <img
                  className="object-scale-down h-40"
                  src={dataProduct.url.replace('tif', 'jpg')}
                  alt="Preview of data product"
                />
              ) : (
                <div className="flex items-center justify-center w-full h-40 bg-white">
                  <span className="sr-only">Preview not available</span>
                  <PhotoIcon className="h-full" />
                </div>
              )}
              <div className="absolute bottom-0 right-0 p-1.5">
                <div className="flex items-center justify-center rounded-full bg-accent2 text-white font-semibold h-8 w-8">
                  {flight.data_products.length}
                </div>
              </div>
            </div>
            {/* flight details */}
            <div className="flex items-center justify-between">
              <div>
                <span className="block text-lg">Sensor: {flight.sensor}</span>
                <HintText>On: {flight.acquisition_date}</HintText>
              </div>
              {projectRole === 'owner' ? (
                <FlightDeleteModal flight={flight} iconOnly={true} />
              ) : null}
            </div>
            {/* action buttons */}
            <div className="flex items-center justify-between gap-2">
              <div className="w-32">
                <LinkOutlineButton
                  size="sm"
                  url={`/projects/${flight.project_id}/flights/${flight.id}/data`}
                >
                  Manage Data
                </LinkOutlineButton>
              </div>
              {projectRole === 'manager' || projectRole === 'owner' ? (
                <div className="w-32">
                  <LinkButton
                    size="sm"
                    url={`/projects/${flight.project_id}/flights/${flight.id}/edit`}
                  >
                    Edit Flight
                  </LinkButton>
                </div>
              ) : null}
            </div>
          </div>
        </Card>
        {/* positions pagination controls below card */}
        <div className="h-16"></div>
      </div>
    </div>
  );
}

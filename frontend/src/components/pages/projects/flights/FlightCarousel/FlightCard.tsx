import { useState } from 'react';
import { PhotoIcon } from '@heroicons/react/24/outline';

import { LinkButton, LinkOutlineButton } from '../../../../Buttons';
import Card from '../../../../Card';
import HintText from '../../../../HintText';
import { Flight } from '../../Project';

import { isGeoTIFF } from '../DataProducts/DataProductsTable';
import { useProjectContext } from '../../ProjectContext';
import FlightDeleteModal from '../FlightDeleteModal';
import MoveFlightModal from '../MoveFlightModal';

export default function FlightCard({ flight }: { flight: Flight }) {
  const [invalidPreviews, setInvalidPreviews] = useState<string[]>([]);
  const { projectRole } = useProjectContext();

  const dataProduct = flight.data_products.length > 0 ? flight.data_products[0] : null;

  return (
    <div className="flex flex-col items-center justify-center">
      <Card rounded={true}>
        <div className="w-[264px] grid grid-flow-row auto-rows-max gap-4">
          <div className="h-8">
            {flight.name && (
              <span className="text-lg font-semibold">{flight.name}</span>
            )}
          </div>
          {/* preview image */}
          <div className="relative flex items-center justify-center bg-accent3/10">
            {dataProduct && isGeoTIFF(dataProduct.data_type) ? (
              <img
                className="object-scale-down h-40"
                src={dataProduct.url.replace('tif', 'jpg')}
                alt="Preview of data product"
              />
            ) : dataProduct &&
              dataProduct.data_type === 'point_cloud' &&
              invalidPreviews.indexOf(dataProduct.id) < 0 ? (
              <img
                className="object-scale-down h-40"
                src={dataProduct.url.replace('copc.laz', 'png')}
                alt="Preview of data product"
                onError={() => {
                  setInvalidPreviews([...invalidPreviews, dataProduct.id]);
                }}
              />
            ) : (
              <div className="flex items-center justify-center w-full h-40 bg-white">
                <span className="sr-only text-center">Preview not available</span>
                <PhotoIcon className="h-40" />
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
            {projectRole === 'owner' && (
              <div className="flex gap-4">
                <MoveFlightModal
                  flightId={flight.id}
                  srcProjectId={flight.project_id}
                />
                <FlightDeleteModal flight={flight} iconOnly={true} />
              </div>
            )}
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
      <div className="h-10"></div>
    </div>
  );
}

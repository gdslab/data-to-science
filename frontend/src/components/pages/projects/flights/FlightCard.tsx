import { Link } from 'react-router-dom';
import { PhotoIcon } from '@heroicons/react/24/outline';

import { Button, OutlineButton } from '../../../Buttons';
import Card from '../../../Card';
import HintText from '../../../HintText';
import { Flight } from '../ProjectDetail';

import { isGeoTIFF } from './dataProducts/DataProducts';

export default function FlightCard({ flight }: { flight: Flight }) {
  const dataProduct = flight.data_products.length > 0 ? flight.data_products[0] : null;

  return (
    <div className="flex items-center justify-center">
      <div className="w-80">
        <Card rounded={true}>
          <div className="grid grid-flow-row auto-rows-max gap-4">
            {/* preview image */}
            <div className="flex items-center relative h-56 bg-black">
              {dataProduct && isGeoTIFF(dataProduct.data_type) ? (
                <img
                  className="w-full"
                  src={dataProduct.url.replace('tif', 'jpg')}
                  alt="Preview of data product"
                />
              ) : (
                <div className="bg-white">
                  <span className="sr-only">Preview not available</span>
                  <PhotoIcon className="w-full" />
                </div>
              )}
              <div className="absolute bottom-0 right-0 p-1.5">
                <div className="flex items-center justify-center rounded-full bg-accent2 text-white font-semibold h-8 w-8">
                  {flight.data_products.length}
                </div>
              </div>
            </div>
            {/* flight details */}
            <div>
              <span className="block text-lg">{flight.sensor}</span>
              <HintText>{flight.acquisition_date}</HintText>
            </div>
            {/* action buttons */}
            <div className="flex items-center justify-between gap-4">
              <div className="w-28">
                <OutlineButton size="sm">
                  <Link to={`/projects/${flight.project_id}/flights/${flight.id}/data`}>
                    Manage
                  </Link>
                </OutlineButton>
              </div>
              <div className="w-28">
                <Button size="sm">Edit</Button>
              </div>
            </div>
          </div>
        </Card>
        {/* positions pagination controls below card */}
        <div className="h-16"></div>
      </div>
    </div>
  );
}
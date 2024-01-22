import { Link } from 'react-router-dom';

import { Button, OutlineButton } from '../../../Buttons';
import Card from '../../../Card';
import HintText from '../../../HintText';
import { Flight } from '../ProjectDetail';

export default function FlightCard({ flight }: { flight: Flight }) {
  return (
    <div className="flex items-center justify-center">
      <div className="w-80">
        <Card rounded={true}>
          <div className="grid grid-flow-row auto-rows-max gap-4">
            {/* preview image */}
            <div className="flex items-center relative h-56 bg-black">
              <img
                src="http://localhost:8000/static/projects/3af69eb6-88cb-4f78-b1cf-c73d50fd8e85/flights/cfa1fcac-9ffd-4d3d-9395-c96288818296/dsm/51b622d3-a310-4bdb-a653-4ebd66717383.jpg"
                title="Data product preview"
              />
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
                    Data
                  </Link>
                </OutlineButton>
              </div>
              <div className="w-28">
                <Button size="sm">Edit</Button>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}

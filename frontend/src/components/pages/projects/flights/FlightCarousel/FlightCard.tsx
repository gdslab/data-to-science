import axios from 'axios';
import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { PhotoIcon, TrashIcon } from '@heroicons/react/24/outline';

import { AlertBar, Status } from '../../../../Alert';
import { LinkButton, LinkOutlineButton } from '../../../../Buttons';
import Card from '../../../../Card';
import { ConfirmationPopup } from '../../../../ConfirmationPopup';
import HintText from '../../../../HintText';
import { Flight } from '../../ProjectDetail';
import Modal from '../../../../Modal';

import { isGeoTIFF } from '../dataProducts/DataProducts';
import { useProjectContext } from '../../ProjectContext';

export default function FlightCard({ flight }: { flight: Flight }) {
  const [openConfirmationPopup, setOpenConfirmationPopup] = useState(false);
  const [status, setStatus] = useState<Status | null>(null);
  const { projectRole } = useProjectContext();
  const params = useParams();
  const navigate = useNavigate();

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
                <div>
                  <div onClick={() => setOpenConfirmationPopup(true)}>
                    <span className="sr-only">Delete</span>
                    <TrashIcon className="w-4 h-4 text-red-600 cursor-pointer" />
                  </div>
                  <Modal
                    open={openConfirmationPopup}
                    setOpen={setOpenConfirmationPopup}
                  >
                    <ConfirmationPopup
                      title="Are you sure you want to deactivate this flight?"
                      content="Deactivating this flight will cause all team and project members to immediately lose access to any data products associated with the flight."
                      confirmText="Yes, deactivate"
                      rejectText="No, keep flight"
                      setOpen={setOpenConfirmationPopup}
                      action={async () => {
                        try {
                          const response = await axios.delete(
                            `/api/v1/projects/${params.projectId}/flights/${flight.id}`
                          );
                          if (response) {
                            setOpenConfirmationPopup(false);
                            navigate(`/projects/${params.projectId}`, {
                              state: { reload: true },
                            });
                          } else {
                            setOpenConfirmationPopup(false);
                            setStatus({
                              type: 'error',
                              msg: 'Unable to deactivate flight',
                            });
                          }
                        } catch (err) {
                          setOpenConfirmationPopup(false);
                          setStatus({
                            type: 'error',
                            msg: 'Unable to deactivate flight',
                          });
                        }
                      }}
                    />
                  </Modal>
                </div>
              ) : null}
            </div>
            {/* action buttons */}
            <div className="flex items-center justify-between gap-4">
              <div className="w-32">
                <LinkOutlineButton
                  size="sm"
                  url={`/projects/${flight.project_id}/flights/${flight.id}/data`}
                >
                  Manage
                </LinkOutlineButton>
              </div>
              {projectRole === 'manager' || projectRole === 'owner' ? (
                <div className="w-32">
                  <LinkButton
                    size="sm"
                    url={`/projects/${flight.project_id}/flights/${flight.id}/edit`}
                  >
                    Edit
                  </LinkButton>
                </div>
              ) : null}
            </div>
          </div>
        </Card>
        {/* positions pagination controls below card */}
        <div className="h-16"></div>
      </div>
      {status ? <AlertBar alertType={status.type}>{status.msg}</AlertBar> : null}
    </div>
  );
}

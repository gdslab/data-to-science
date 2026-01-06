import { useState } from 'react';
import { useParams } from 'react-router';
import { LockClosedIcon, LockOpenIcon } from '@heroicons/react/24/outline';

import { Button } from '../../../../../Buttons';
import Modal from '../../../../../Modal';
import { DataProduct } from '../../Project';
import { useProjectContext } from '../../ProjectContext';
import ShareControls from '../../../../../maps/RasterSymbologySettings/RasterSymbologyAccessControls';

export default function DataProductShareModal({
  dataProduct,
  iconOnly = true,
  tableView = false,
}: {
  dataProduct: DataProduct;
  iconOnly?: boolean;
  tableView?: boolean;
}) {
  const [openShareModal, setOpenShareModal] = useState(false);
  const { projectId, flightId } = useParams();

  const { project } = useProjectContext();

  if (project) {
    return (
      <div>
        <div>
          {tableView ? (
            <div
              className="flex items-center text-sky-600 text-sm cursor-pointer"
              onClick={() => setOpenShareModal(true)}
            >
              <div className="relative rounded-full accent3 p-1 focus:outline-hidden">
                {dataProduct.public ? (
                  <LockOpenIcon className="w-4 w-4" />
                ) : (
                  <LockClosedIcon className="w-4 w-4" />
                )}
              </div>
              <span>Share</span>
            </div>
          ) : iconOnly ? (
            <div
              className="cursor-pointer"
              onClick={() => setOpenShareModal(true)}
            >
              <span className="sr-only">Share</span>
              {dataProduct.public ? (
                <LockOpenIcon className="w-5 w-5 cursor-pointer hover:scale-110" />
              ) : (
                <LockClosedIcon className="w-5 w-5 cursor-pointer hover:scale-110" />
              )}
            </div>
          ) : (
            <Button
              type="button"
              icon="trash"
              onClick={() => setOpenShareModal(true)}
            >
              Share
            </Button>
          )}
        </div>
        <Modal open={openShareModal} setOpen={setOpenShareModal}>
          <ShareControls
            dataProduct={dataProduct}
            project={project}
            refreshUrl={`/projects/${projectId}/flights/${flightId}/data`}
          />
        </Modal>
      </div>
    );
  } else {
    return null;
  }
}

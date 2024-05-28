import axios from 'axios';
import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { TrashIcon } from '@heroicons/react/24/outline';

import { AlertBar, Status } from '../../../Alert';
import { Button } from '../../../Buttons';
import { ConfirmationPopup } from '../../../ConfirmationPopup';
import Modal from '../../../Modal';
import { FieldCampaign } from '../Project';

export default function FieldCampaignDeleteModal({
  campaign,
  iconOnly = true,
  tableView = false,
}: {
  campaign: FieldCampaign;
  iconOnly?: boolean;
  tableView?: boolean;
}) {
  const [openConfirmationPopup, setOpenConfirmationPopup] = useState(false);
  const [status, setStatus] = useState<Status | null>(null);
  const params = useParams();
  const navigate = useNavigate();

  return (
    <div>
      <div>
        {tableView ? (
          <div
            className="flex items-center text-sky-600 text-sm cursor-pointer"
            onClick={() => setOpenConfirmationPopup(true)}
          >
            <div className="relative rounded-full accent3 p-1 focus:outline-none">
              <TrashIcon className="w-4 h-4" />
            </div>
            <span>Delete</span>
          </div>
        ) : iconOnly ? (
          <div
            className="cursor-pointer"
            onClick={() => setOpenConfirmationPopup(true)}
          >
            <span className="sr-only">Delete</span>
            <TrashIcon className="w-5 h-5 cursor-pointer" />
          </div>
        ) : (
          <Button
            type="button"
            icon="trash"
            onClick={() => setOpenConfirmationPopup(true)}
          >
            Deactivate campaign
          </Button>
        )}
      </div>
      <Modal open={openConfirmationPopup} setOpen={setOpenConfirmationPopup}>
        <ConfirmationPopup
          title="Are you sure you want to deactivate this campaign?"
          content="Deactivating this campaign will cause all team and project members to immediately lose access to any templates associated with the campaign."
          confirmText="Yes, deactivate"
          rejectText="No, keep campaign"
          setOpen={setOpenConfirmationPopup}
          action={async () => {
            setStatus(null);
            try {
              const response = await axios.delete(
                `/api/v1/projects/${params.projectId}/campaigns/${campaign.id}`
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
                  msg: 'Unable to deactivate campaign',
                });
              }
            } catch (err) {
              setOpenConfirmationPopup(false);
              setStatus({
                type: 'error',
                msg: 'Unable to deactivate campaign',
              });
            }
          }}
        />
      </Modal>
      {status ? <AlertBar alertType={status.type}>{status.msg}</AlertBar> : null}
    </div>
  );
}

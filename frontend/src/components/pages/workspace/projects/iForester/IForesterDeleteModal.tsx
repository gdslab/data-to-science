import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { TrashIcon } from '@heroicons/react/24/outline';

import { AlertBar, Status } from '../../../../Alert';
import { Button } from '../../../../Buttons';
import { ConfirmationPopup } from '../../../../ConfirmationPopup';
import Modal from '../../../../Modal';
import { IForester } from '../Project';

import api from '../../../../api';

export default function IForesterDeleteModal({
  iforester,
  iconOnly = true,
  tableView = false,
}: {
  iforester: IForester;
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
            <TrashIcon className="w-5 h-5 cursor-pointer hover:scale-110" />
          </div>
        ) : (
          <Button
            type="button"
            icon="trash"
            onClick={() => setOpenConfirmationPopup(true)}
          >
            Delete submission
          </Button>
        )}
      </div>
      <Modal open={openConfirmationPopup} setOpen={setOpenConfirmationPopup}>
        <ConfirmationPopup
          title="Are you sure you want to delete this submission?"
          content="Deleting this submission will cause all team and project members to immediately lose access to it."
          confirmText="Yes, delete"
          rejectText="No, keep submission"
          setOpen={setOpenConfirmationPopup}
          onConfirm={async () => {
            setStatus(null);
            try {
              const response = await api.delete(
                `/projects/${params.projectId}/iforester/${iforester.id}`
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
                  msg: 'Unable to delete submission',
                });
              }
            } catch (err) {
              setOpenConfirmationPopup(false);
              setStatus({
                type: 'error',
                msg: 'Unable to delete submission',
              });
            }
          }}
        />
      </Modal>
      {status ? (
        <AlertBar alertType={status.type}>{status.msg}</AlertBar>
      ) : null}
    </div>
  );
}

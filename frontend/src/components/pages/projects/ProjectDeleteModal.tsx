import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AlertBar, Status } from '../../Alert';
import { Button } from '../../Buttons';
import { ConfirmationPopup } from '../../ConfirmationPopup';
import Modal from '../../Modal';
import { ProjectDetail } from './Project';

import api from '../../../api';

export default function ProjectDeleteModal({ project }: { project: ProjectDetail }) {
  const [openConfirmationPopup, setOpenConfirmationPopup] = useState(false);
  const [status, setStatus] = useState<Status | null>(null);
  const navigate = useNavigate();

  return (
    <div>
      <div className="w-48">
        <Button
          type="button"
          size="sm"
          onClick={() => setOpenConfirmationPopup(true)}
        >
          Deactivate project
        </Button>
      </div>
      <Modal open={openConfirmationPopup} setOpen={setOpenConfirmationPopup}>
        <ConfirmationPopup
          title="Are you sure you want to deactivate this project?"
          content="Deactivating this project will cause all team and project members to immediately lose access to any flights, and data associated with the project."
          confirmText="Yes, deactivate"
          rejectText="No, keep project"
          setOpen={setOpenConfirmationPopup}
          onConfirm={async () => {
            setStatus(null);
            try {
              const response = await api.delete(`/projects/${project.id}`);
              if (response) {
                setOpenConfirmationPopup(false);
                navigate('/projects', {
                  state: { reload: true },
                });
              } else {
                setOpenConfirmationPopup(false);
                setStatus({
                  type: 'error',
                  msg: 'Unable to deactivate project',
                });
              }
            } catch (err) {
              setOpenConfirmationPopup(false);
              setStatus({
                type: 'error',
                msg: 'Unable to deactivate project',
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

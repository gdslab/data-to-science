import { AxiosResponse, isAxiosError } from 'axios';
import { useEffect, useState } from 'react';
import Select from 'react-select';
import { useRevalidator } from 'react-router-dom';
import { FolderIcon } from '@heroicons/react/24/outline';

import { AlertBar, Status } from '../../../Alert';
import { Flight, ProjectItem } from '../Project';
import Modal from '../../../Modal';
import { Button } from '../../../Buttons';

import api from '../../../../api';

type ProjectOption = {
  label: string;
  value: string;
};

export default function MoveFlightModal({
  flightId,
  srcProjectId,
  tableView,
}: {
  flightId: string;
  srcProjectId: string;
  tableView?: boolean;
}) {
  const [dstProjectId, setDstProjectId] = useState('');
  const [isMoving, setIsMoving] = useState(false);
  const [projectOptions, setProjectOptions] = useState<ProjectOption[]>([]);
  const [open, setOpen] = useState(false);
  const [status, setStatus] = useState<Status | null>(null);

  const revalidator = useRevalidator();

  useEffect(() => {
    setIsMoving(false);
    setStatus(null);
  }, [open]);

  useEffect(() => {
    async function getProjects() {
      const response: AxiosResponse<ProjectItem[]> = await api.get(`/projects`);
      if (response) {
        const ownedProjects = response.data
          .filter(({ id, role }) => role === 'owner' && id !== srcProjectId)
          .map((project) => ({ label: project.title, value: project.id }));
        setDstProjectId(ownedProjects.length > 0 ? ownedProjects[0].value : '');
        setProjectOptions(ownedProjects);
      } else {
        return [];
      }
    }
    if (open) getProjects();
  }, [open]);

  async function moveProject() {
    try {
      setIsMoving(true);
      const response: AxiosResponse<Flight> = await api.put(
        `/projects/${srcProjectId}/flights/${flightId}/move_to_project/${dstProjectId}`
      );
      if (response.status === 200) {
        revalidator.revalidate();
        setIsMoving(false);
        setOpen(false);
      } else {
        setIsMoving(false);
        setStatus({ type: 'error', msg: 'Unable to move flight at this time' });
      }
    } catch (err) {
      setIsMoving(false);
      if (isAxiosError(err) && err.response && err.response.data.detail) {
        if (typeof err.response.data.detail === 'string') {
          setStatus({ type: 'error', msg: err.response.data.detail });
        } else if (typeof (err.response.status === 422)) {
          setStatus({ type: 'error', msg: err.response.data.detail[0].msg });
        } else {
          setStatus({
            type: 'error',
            msg: 'Unable to move flight at this time',
          });
        }
      } else {
        setStatus({ type: 'error', msg: 'Unable to move flight at this time' });
      }
    }
  }

  return (
    <div>
      {tableView ? (
        <div
          className="flex items-center text-sky-600 cursor-pointer"
          onClick={() => setOpen(true)}
        >
          <div className="rounded-full accent3 p-1 focus:outline-hidden">
            <FolderIcon className="w-4 h-4" />
          </div>
          <span>Move</span>
        </div>
      ) : (
        <button onClick={() => setOpen(true)}>
          <FolderIcon className="h-5 w-5" />
        </button>
      )}
      <Modal open={open} setOpen={setOpen}>
        <div className="m-4 h-64 flex flex-col justify-between">
          <div>
            <span className="text-gray-600 font-semibold">
              Select the project you are moving the flight to:
            </span>
            <Select
              styles={{
                input: (base) => ({
                  ...base,
                  'input:focus': {
                    boxShadow: 'none',
                  },
                }),
              }}
              theme={(theme) => ({
                ...theme,
                colors: {
                  ...theme.colors,
                  primary: '#3d5a80',
                  primary25: '#e2e8f0',
                },
              })}
              isSearchable
              defaultValue={projectOptions[0]}
              maxMenuHeight={120}
              options={projectOptions}
              onChange={(dstProject) => {
                if (dstProject && dstProject.value) {
                  setDstProjectId(dstProject.value);
                }
              }}
            />
          </div>
          <Button
            type="button"
            disabled={dstProjectId.length === 0}
            onClick={() => moveProject()}
          >
            {isMoving ? 'Moving...' : 'Move'}
          </Button>
          {status && <AlertBar alertType={status.type}>{status.msg}</AlertBar>}
        </div>
      </Modal>
    </div>
  );
}

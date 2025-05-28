import { useEffect, useState } from 'react';

import { Button } from '../../../Buttons';
import { IndoorProjectAPIResponse } from './IndoorProject';
import IndoorProjectCard from './IndoorProjectCard';
import Modal from '../../../Modal';
import PaginationList from '../PaginationList';
import IndoorProjectForm from './IndoorProjectForm';

import { useProjectContext } from '../projects/ProjectContext';

function IndoorProjectListHeader() {
  const [open, setOpen] = useState(false);

  const { locationDispatch } = useProjectContext();

  useEffect(() => {
    locationDispatch({ type: 'clear', payload: null });
  }, [open]);

  return (
    <div className="flex flex-col gap-4">
      <h1>Indoor Projects</h1>
      <div className="flex gap-4 justify-between">
        <div className="w-96">
          <Button icon="folderplus" onClick={() => setOpen(true)}>
            Create
          </Button>
          <Modal open={open} setOpen={setOpen}>
            <IndoorProjectForm setModalOpen={setOpen} />
          </Modal>
        </div>
      </div>
    </div>
  );
}

type IndoorProjectListProps = {
  indoorProjects: IndoorProjectAPIResponse[] | null;
};

export default function IndoorProjectList({
  indoorProjects,
}: IndoorProjectListProps) {
  if (!indoorProjects) return null;

  return (
    <PaginationList dataList={indoorProjects}>
      <IndoorProjectListHeader />
      <div className="flex flex-1 flex-wrap gap-4 pb-24 overflow-y-auto">
        {indoorProjects.map((indoorProject) => (
          <div key={indoorProject.id} className="block h-40">
            <IndoorProjectCard indoorProject={indoorProject} />
          </div>
        ))}
      </div>
    </PaginationList>
  );
}

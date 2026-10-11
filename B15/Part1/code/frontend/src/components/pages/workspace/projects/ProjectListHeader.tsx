import { useEffect, useState } from 'react';

import { Button } from '../../../Buttons';
import Modal from '../../../Modal';
import ProjectForm from './ProjectForm';

import { useProjectContext } from './ProjectContext';

export default function ProjectListHeader() {
  const [open, setOpen] = useState(false);

  const { locationDispatch } = useProjectContext();

  useEffect(() => {
    locationDispatch({ type: 'clear', payload: null });
  }, [locationDispatch, open]);

  return (
    <div className="flex flex-col gap-4">
      <h1>Projects</h1>
      <div className="w-96">
        <Button icon="folderplus" onClick={() => setOpen(true)}>
          Create
        </Button>
        <Modal open={open} setOpen={setOpen}>
          <ProjectForm setModalOpen={setOpen} />
        </Modal>
      </div>
    </div>
  );
}

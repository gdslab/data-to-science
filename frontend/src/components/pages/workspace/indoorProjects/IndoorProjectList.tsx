import { useEffect, useMemo, useState } from 'react';

import { Button } from '../../../Buttons';
import { IndoorProjectAPIResponse } from './IndoorProject';
import IndoorProjectCard from './IndoorProjectCard';
import Modal from '../../../Modal';
import Pagination from '../../../Pagination';
import IndoorProjectForm from './IndoorProjectForm';

import { useProjectContext } from '../projects/ProjectContext';

function IndoorProjectListHeader() {
  const [open, setOpen] = useState(false);

  const { locationDispatch } = useProjectContext();

  useEffect(() => {
    locationDispatch({ type: 'clear', payload: null });
  }, [locationDispatch, open]);

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
  const [currentPage, setCurrentPage] = useState(0);

  const MAX_ITEMS = 12;

  /**
   * Updates the current selected pagination page.
   * @param newPage Index of new page.
   */
  function updateCurrentPage(newPage: number): void {
    if (!indoorProjects) {
      setCurrentPage(0);
      return;
    }

    const total_pages = Math.ceil(indoorProjects.length / MAX_ITEMS);

    if (newPage + 1 > total_pages) {
      setCurrentPage(total_pages - 1);
    } else if (newPage < 0) {
      setCurrentPage(0);
    } else {
      setCurrentPage(newPage);
    }
  }

  // Reset to first page if current page becomes invalid
  useEffect(() => {
    if (indoorProjects) {
      const total_pages = Math.ceil(indoorProjects.length / MAX_ITEMS);
      if (currentPage >= total_pages && total_pages > 0) {
        setCurrentPage(0);
      }
    }
  }, [indoorProjects, currentPage]);

  const paginatedProjects = useMemo(() => {
    if (!indoorProjects) {
      return [];
    }

    return indoorProjects.slice(
      currentPage * MAX_ITEMS,
      MAX_ITEMS + currentPage * MAX_ITEMS
    );
  }, [indoorProjects, currentPage]);

  const TOTAL_PAGES = Math.ceil(
    indoorProjects ? indoorProjects.length / MAX_ITEMS : 0
  );

  if (!indoorProjects) return null;

  return (
    <div className="flex flex-col gap-4 pt-4 px-4 h-full overflow-hidden">
      <IndoorProjectListHeader />
      {indoorProjects.length > 0 && (
        <div className="flex-1 min-h-0 flex flex-wrap gap-4 pb-24 overflow-y-auto">
          {paginatedProjects.map((indoorProject) => (
            <div key={indoorProject.id} className="block h-40">
              <IndoorProjectCard indoorProject={indoorProject} />
            </div>
          ))}
        </div>
      )}
      {/* Pagination */}
      {indoorProjects.length > 0 && (
        <div className="w-full bg-slate-200 fixed bottom-0 left-0 right-0 py-4 px-6 z-10">
          <div className="flex justify-center">
            <Pagination
              currentPage={currentPage}
              totalPages={TOTAL_PAGES}
              updateCurrentPage={updateCurrentPage}
            />
          </div>
        </div>
      )}
    </div>
  );
}

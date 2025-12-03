import { ReactElement, useCallback, useEffect } from 'react';
import { useLocation } from 'react-router';
import {
  ArrowUturnLeftIcon,
  Bars3Icon,
  XMarkIcon,
} from '@heroicons/react/24/outline';

import { useMapContext } from '../MapContext';

import ActiveProjectPane from './ActiveProjectPane';
import LoadingBars from '../../LoadingBars';
import ProjectsPane from './ProjectsPane';

type LayerPaneProps = {
  hidePane: boolean;
  toggleHidePane: React.Dispatch<React.SetStateAction<boolean>>;
};

export default function LayerPane({
  hidePane,
  toggleHidePane,
}: LayerPaneProps) {
  const {
    activeDataProduct,
    activeDataProductDispatch,
    activeMapTool,
    activeMapToolDispatch,
    activeProject,
    activeProjectDispatch,
    projects,
    projectsLoaded,
  } = useMapContext();

  const { state } = useLocation();

  // Hide the pane when a point cloud is active or when the compare tool is active
  useEffect(() => {
    if (
      (activeDataProduct &&
        (activeDataProduct.data_type === 'point_cloud' ||
          activeDataProduct.data_type === 'panoramic' ||
          activeDataProduct.data_type === '3dgs')) ||
      activeMapTool === 'compare'
    ) {
      toggleHidePane(true);
    }
  }, [activeDataProduct, activeMapTool, toggleHidePane]);

  // Set the active project and data product when a user navigates to
  // homepage with a project and data product in the URL (e.g. from a
  // DataProductCard)
  useEffect(() => {
    if (state && state.project && state.dataProduct) {
      activeDataProductDispatch({ type: 'set', payload: state.dataProduct });
      activeProjectDispatch({ type: 'set', payload: state.project });
    }
  }, [activeDataProductDispatch, activeProjectDispatch, state]);

  // Clear the active project and data product when the user backs
  // out of the active project pane
  const handleReturnClick = useCallback(() => {
    activeMapToolDispatch({ type: 'set', payload: 'map' });
    activeDataProductDispatch({ type: 'clear', payload: null });
    activeProjectDispatch({ type: 'clear', payload: null });
  }, [activeDataProductDispatch, activeMapToolDispatch, activeProjectDispatch]);

  // Toggle the left pane
  const handleToggleClick = useCallback(() => {
    toggleHidePane((prev) => !prev);
  }, [toggleHidePane]);

  let content: ReactElement;

  if (projectsLoaded === 'loading') {
    content = (
      <div className="h-full w-full flex flex-col items-center justify-center">
        <span className="text-lg italic text-gray-700 font-semibold">
          Checking for projects...
        </span>
        <LoadingBars />
      </div>
    );
  } else if (projectsLoaded === 'error') {
    content = (
      <div className="h-full w-full flex flex-col items-center justify-center">
        <span className="text-lg italic text-red-600 font-semibold">
          Failed to load projects.
        </span>
        <span className="text-sm text-red-600 font-light">
          An unexpected error occurred while retrieving your projects.
        </span>
      </div>
    );
  } else if (projectsLoaded === 'loaded') {
    content = (
      <div className="h-full flex flex-col">
        <div className="h-full text-slate-700">
          <div className="h-11 flex items-center justify-between p-2.5">
            {activeProject ? (
              <button type="button" onClick={handleReturnClick}>
                <ArrowUturnLeftIcon className="h-6 w-6 cursor-pointer" />
              </button>
            ) : (
              <span />
            )}
            <XMarkIcon
              className="h-6 w-6 cursor-pointer float-right"
              onClick={handleToggleClick}
            />
          </div>
          {activeProject ? (
            <ActiveProjectPane project={activeProject} />
          ) : (
            <ProjectsPane projects={projects} />
          )}
        </div>
      </div>
    );
  } else if (projectsLoaded === 'initial') {
    content = <></>;
  } else {
    content = (
      <div className="h-full w-full flex items-center justify-center">
        <span className="text-lg italic text-gray-700">
          Unexpected state has occurred.
        </span>
      </div>
    );
  }

  return hidePane ? (
    <div className="flex items-center justify-between p-2.5 text-slate-700">
      <button type="button" onClick={handleToggleClick}>
        <Bars3Icon className="h-6 w-6 cursor-pointers" />
      </button>
    </div>
  ) : (
    content
  );
}

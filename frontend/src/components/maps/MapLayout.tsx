import axios from 'axios';
import { useState } from 'react';
import { useLoaderData } from 'react-router-dom';

import LayerPane from './LayerPane';
import Map from './Map';
import { Project } from '../pages/projects/ProjectList';

import { MapContextProvider } from './MapContext';

export async function loader() {
  const response = await axios.get('/api/v1/projects');
  if (response) {
    return response.data;
  } else {
    return [];
  }
}

function classNames(...classes: [string, string]) {
  return classes.filter(Boolean).join(' ');
}

export default function MapLayout() {
  const projects = useLoaderData() as Project[];
  const [hidePane, toggleHidePane] = useState(false);

  return (
    <MapContextProvider>
      {/* sidebar */}
      <div className="flex flex-row h-full">
        <div
          className={classNames(
            hidePane ? 'w-[48px] ease-out duration-200' : 'w-[450px]',
            'shrink-0 bg-slate-100'
          )}
        >
          <LayerPane
            hidePane={hidePane}
            projects={projects}
            toggleHidePane={toggleHidePane}
          />
        </div>
        {/* page content */}
        <div className="w-full">
          <Map projects={projects} />
        </div>
      </div>
    </MapContextProvider>
  );
}

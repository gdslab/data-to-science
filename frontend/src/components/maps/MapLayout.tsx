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
      <div
        className={classNames(
          hidePane ? 'w-[48px]' : 'w-[500px]',
          'z-10 fixed left-0 h-full bg-slate-100 text-slate-200'
        )}
      >
        <LayerPane
          hidePane={hidePane}
          projects={projects}
          toggleHidePane={toggleHidePane}
        />
      </div>
      {/* page content */}
      <div className="w-full h-full bg-slate-700">
        <Map projects={projects} />
      </div>
    </MapContextProvider>
  );
}

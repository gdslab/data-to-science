import { AxiosResponse, isAxiosError } from 'axios';
import { useEffect, useState } from 'react';
import { useLocation, useParams } from 'react-router';
import { Tab, TabGroup, TabList, TabPanel, TabPanels } from '@headlessui/react';

import { LinkButton } from '../../Buttons';
import BreedBase from './breedBase/BreedBase';
import { IForester, ProjectModule } from './Project';
import ProjectCampaigns from './ProjectCampaigns';
import ProjectFlights from './ProjectFlights';
import ProjectVectorData from './ProjectVectorData';

import api from '../../../api';

import iForesterLogo from '../../../assets/iForester-logo.png';

export default function ProjectTabNav({
  project_modules,
}: {
  project_modules: ProjectModule[];
}) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [iforesterData, setIForesterData] = useState<IForester[]>([]);

  const location = useLocation();
  const params = useParams();

  useEffect(() => {
    if (location.state && location.state.selectedIndex) {
      setSelectedIndex(location.state.selectedIndex);
    }
  }, [location.state]);

  useEffect(() => {
    async function fetchIForesterData(projectId: string) {
      try {
        const response: AxiosResponse<IForester[]> = await api.get(
          `/projects/${projectId}/iforester`
        );
        if (response.status === 200) {
          setIForesterData(response.data);
        } else {
          return [];
        }
      } catch (err) {
        if (isAxiosError(err) && err.response) {
          console.error(err.response.data);
        } else {
          console.error(err);
        }
        return [];
      }
    }
    if (params.projectId) {
      fetchIForesterData(params.projectId);
    }
  }, [params.projectId]);

  // Sort modules by sort_order and filter enabled ones
  const enabledModules = project_modules
    .filter((module) => {
      // Only show iForester if there is data
      if (module.module_name === 'iforester') {
        return module.enabled && iforesterData.length > 0;
      }
      return module.enabled;
    })
    .sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));

  // Map module names to their corresponding components
  const getModuleComponent = (moduleName: string) => {
    switch (moduleName) {
      case 'flights':
        return <ProjectFlights />;
      case 'map_layers':
        return <ProjectVectorData />;
      case 'field_data':
        return <ProjectCampaigns />;
      case 'iforester':
        return (
          <LinkButton url={`/projects/${params.projectId}/iforester`}>
            Go to iForester page
          </LinkButton>
        );
      case 'breedbase':
        return <BreedBase />;
      default:
        return null;
    }
  };

  return (
    <TabGroup selectedIndex={selectedIndex} onChange={setSelectedIndex}>
      <TabList>
        {enabledModules.map((module) => (
          <Tab
            key={module.module_name}
            className="data-selected:bg-accent3 data-selected:text-white data-hover:underline w-28 shrink-0 rounded-lg p-2 font-medium"
          >
            {module.module_name === 'iforester' ? (
              <div className="flex items-center justify-center gap-2">
                <img src={iForesterLogo} className="h-4 w-4" />
                {module.label || 'iForester'}
              </div>
            ) : (
              module.label || module.module_name
            )}
          </Tab>
        ))}
      </TabList>
      <hr className="my-4 border-gray-700" />
      <TabPanels>
        {enabledModules.map((module) => (
          <TabPanel key={module.module_name}>
            {getModuleComponent(module.module_name)}
          </TabPanel>
        ))}
      </TabPanels>
    </TabGroup>
  );
}

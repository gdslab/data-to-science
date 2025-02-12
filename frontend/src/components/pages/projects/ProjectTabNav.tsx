import { AxiosResponse, isAxiosError } from 'axios';
import { useEffect, useState } from 'react';
import { useLocation, useParams } from 'react-router-dom';
import { Tab, TabGroup, TabList, TabPanel, TabPanels } from '@headlessui/react';

import { LinkButton } from '../../Buttons';
import { IForester } from './Project';
import ProjectCampaigns from './ProjectCampaigns';
import ProjectFlights from './ProjectFlights';
import ProjectVectorData from './ProjectVectorData';

import api from '../../../api';

import iForesterLogo from '../../../assets/iForester-logo.png';

export default function ProjectTabNav() {
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
  }, []);

  return (
    <TabGroup selectedIndex={selectedIndex} onChange={setSelectedIndex}>
      <TabList>
        <Tab className="data-[selected]:bg-accent3 data-[selected]:text-white data-[hover]:underline w-28 shrink-0 rounded-lg p-2 font-medium">
          Flights
        </Tab>
        <Tab className="data-[selected]:bg-accent3 data-[selected]:text-white data-[hover]:underline w-28 shrink-0 rounded-lg p-2 font-medium">
          Map Layers
        </Tab>
        <Tab className="data-[selected]:bg-accent3 data-[selected]:text-white data-[hover]:underline w-28 shrink-0 rounded-lg p-2 font-medium">
          Field Data
        </Tab>
        {iforesterData.length > 0 && (
          <Tab className="data-[selected]:bg-accent3 data-[selected]:text-white data-[hover]:underline w-28 shrink-0 rounded-lg p-2 font-medium">
            <div className="flex items-center justify-center gap-2">
              <img src={iForesterLogo} className="h-4 w-4" />
              iForester
            </div>
          </Tab>
        )}
      </TabList>
      <hr className="my-4 border-gray-700" />
      <TabPanels>
        <TabPanel>
          <ProjectFlights />
        </TabPanel>
        <TabPanel>
          <ProjectVectorData />
        </TabPanel>
        <TabPanel>
          <ProjectCampaigns />
        </TabPanel>
        {iforesterData.length > 0 && (
          <TabPanel>
            <LinkButton url={`/projects/${params.projectId}/iforester`}>
              Go to iForester page
            </LinkButton>
          </TabPanel>
        )}
      </TabPanels>
    </TabGroup>
  );
}

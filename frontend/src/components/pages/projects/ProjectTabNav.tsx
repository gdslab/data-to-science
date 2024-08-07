import { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { Tab, TabGroup, TabList, TabPanel, TabPanels } from '@headlessui/react';

import ProjectCampaigns from './ProjectCampaigns';
import ProjectFlights from './ProjectFlights';
import ProjectVectorData from './ProjectVectorData';

export default function ProjectTabNav() {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const location = useLocation();

  useEffect(() => {
    if (location.state && location.state.selectedIndex) {
      setSelectedIndex(location.state.selectedIndex);
    }
  }, [location.state]);

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
      </TabPanels>
    </TabGroup>
  );
}

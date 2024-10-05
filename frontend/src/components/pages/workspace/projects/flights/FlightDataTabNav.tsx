import { useState } from 'react';
import { Tab, TabGroup, TabList, TabPanel, TabPanels } from '@headlessui/react';

import DataProducts from './DataProducts';
import RawData from './RawData';
import { FlightData } from './FlightData';

function getFlightDataTabSelectionFromLS(): number {
  const flightDataTabSelection = localStorage.getItem('flightDataTabSelection');
  if (flightDataTabSelection) {
    if (
      parseInt(flightDataTabSelection) === 0 ||
      parseInt(flightDataTabSelection) === 1
    ) {
      return parseInt(flightDataTabSelection);
    } else {
      return 0;
    }
  } else {
    return 0;
  }
}

export default function FlightDataTabNav({ dataProducts, rawData }: FlightData) {
  const [selectedIndex, setSelectedIndex] = useState(getFlightDataTabSelectionFromLS());

  function onChange(index: number) {
    localStorage.setItem('flightDataTabSelection', index.toString());
    setSelectedIndex(index);
  }

  return (
    <TabGroup selectedIndex={selectedIndex} onChange={onChange}>
      <TabList>
        <Tab className="data-[selected]:bg-accent3 data-[selected]:text-white data-[hover]:underline focus:outline-none focus:ring focus:ring-sky-300 w-32 shrink-0 rounded-lg p-2 font-medium">
          Data Products
        </Tab>
        <Tab className="data-[selected]:bg-accent3 data-[selected]:text-white data-[hover]:underline focus:outline-none focus:ring focus:ring-sky-300 w-32 shrink-0 rounded-lg p-2 font-medium">
          Raw Data
        </Tab>
      </TabList>
      <hr className="my-4 border-gray-700" />
      <TabPanels>
        <TabPanel>
          <DataProducts data={dataProducts} />
        </TabPanel>
        <TabPanel>
          {/* <RawData data={rawData} open={open} setOpen={setOpen} /> */}
          <RawData rawData={rawData} />
        </TabPanel>
      </TabPanels>
    </TabGroup>
  );
}

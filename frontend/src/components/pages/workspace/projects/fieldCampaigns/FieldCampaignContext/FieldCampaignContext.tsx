import { AxiosResponse } from 'axios';
import { createContext, useContext, useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';

import { FieldCampaign } from '../../Project';
import { useProjectContext } from '../../ProjectContext';

import api from '../../../../../../api';

type Context = {
  fieldCampaign: FieldCampaign | null;
  updateFieldCampaign: (fieldCampaign: FieldCampaign | null) => void;
  selectedTimepoints: string[];
  addSelectedTimepoint: (timepoint: string) => void;
  addSelectedTimepoints: (timepoints: string[]) => void;
  removeSelectedTimepoint: (timepoint: string) => void;
  resetSelectedTimepoints: () => void;
};

const context: Context = {
  fieldCampaign: null,
  updateFieldCampaign: () => {},
  selectedTimepoints: [],
  addSelectedTimepoint: () => {},
  addSelectedTimepoints: () => {},
  removeSelectedTimepoint: () => {},
  resetSelectedTimepoints: () => {},
};

const FieldCampaignContext = createContext(context);

type ContextProvider = { children: React.ReactNode };

export function FieldCampaignContextProvider({ children }: ContextProvider) {
  const [fieldCampaign, setCampaign] = useState<FieldCampaign | null>(null);
  const [selectedTimepoints, setSelectedTimepoints] = useState<string[]>([]);

  const { projectId } = useParams();

  const { project } = useProjectContext();

  useEffect(() => {
    async function fetchFieldCampaign() {
      try {
        const response: AxiosResponse<FieldCampaign | null> = await api.get(
          `/projects/${projectId}/campaigns`
        );
        if (response) {
          updateFieldCampaign(response.data);
        } else {
          updateFieldCampaign(null);
        }
      } catch (_err) {
        console.log('unable to retrieve campaign');
        updateFieldCampaign(null);
      }
    }

    if (projectId) {
      fetchFieldCampaign();
    }
  }, [project]);

  function updateFieldCampaign(fieldCampaign: FieldCampaign | null) {
    setCampaign(fieldCampaign);
  }

  function addSelectedTimepoint(newSelectedTimepoint: string) {
    setSelectedTimepoints([...selectedTimepoints, newSelectedTimepoint]);
  }

  function addSelectedTimepoints(newSelectedTimepoints: string[]) {
    setSelectedTimepoints(newSelectedTimepoints);
  }

  function removeSelectedTimepoint(removeSelectedTimepoint: string) {
    const currentSelectedTimepoints = selectedTimepoints.slice();
    const removeIdx = currentSelectedTimepoints.indexOf(
      removeSelectedTimepoint
    );
    // if index found, use filter to remove it from selected timepoints array
    if (removeIdx > -1) {
      setSelectedTimepoints([
        ...currentSelectedTimepoints.filter((_, index) => index !== removeIdx),
      ]);
    }
  }

  function resetSelectedTimepoints() {
    setSelectedTimepoints([]);
  }

  return (
    <FieldCampaignContext.Provider
      value={{
        fieldCampaign,
        updateFieldCampaign,
        selectedTimepoints,
        addSelectedTimepoint,
        addSelectedTimepoints,
        removeSelectedTimepoint,
        resetSelectedTimepoints,
      }}
    >
      {children}
    </FieldCampaignContext.Provider>
  );
}

export function useFieldCampaignContext() {
  return useContext(FieldCampaignContext);
}

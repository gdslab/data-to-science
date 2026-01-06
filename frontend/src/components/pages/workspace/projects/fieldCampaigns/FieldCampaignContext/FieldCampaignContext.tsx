import { AxiosResponse } from 'axios';
import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { useParams } from 'react-router';

import { FieldCampaign } from '../../Project';

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

  const updateFieldCampaign = useCallback((fieldCampaign: FieldCampaign | null) => {
    setCampaign(fieldCampaign);
  }, []);

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
      } catch {
        console.log('unable to retrieve campaign');
        updateFieldCampaign(null);
      }
    }

    if (projectId) {
      fetchFieldCampaign();
    }
  }, [projectId, updateFieldCampaign]);

  const addSelectedTimepoint = useCallback((newSelectedTimepoint: string) => {
    setSelectedTimepoints((prev) => [...prev, newSelectedTimepoint]);
  }, []);

  const addSelectedTimepoints = useCallback((newSelectedTimepoints: string[]) => {
    setSelectedTimepoints(newSelectedTimepoints);
  }, []);

  const removeSelectedTimepoint = useCallback((removeSelectedTimepoint: string) => {
    setSelectedTimepoints((prev) => {
      const currentSelectedTimepoints = prev.slice();
      const removeIdx = currentSelectedTimepoints.indexOf(
        removeSelectedTimepoint
      );
      // if index found, use filter to remove it from selected timepoints array
      if (removeIdx > -1) {
        return currentSelectedTimepoints.filter((_, index) => index !== removeIdx);
      }
      return prev;
    });
  }, []);

  const resetSelectedTimepoints = useCallback(() => {
    setSelectedTimepoints([]);
  }, []);

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

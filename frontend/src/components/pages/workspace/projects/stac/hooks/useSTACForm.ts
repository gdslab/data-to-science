import { useState, useEffect } from 'react';
import { STACMetadata } from '../STACTypes';

interface FormState {
  sciDoi: string;
  sciCitation: string;
  license: string;
  customTitles: Record<string, string>;
}

interface STACRequestPayload {
  sci_doi?: string;
  sci_citation?: string;
  license?: string;
  custom_titles?: Record<string, string>;
}

interface UseSTACFormReturn {
  formState: FormState;
  updateFormField: <K extends keyof FormState>(
    field: K,
    value: FormState[K]
  ) => void;
  buildRequestPayload: () => STACRequestPayload;
  resetForm: () => void;
}

const DEFAULT_LICENSE = 'CC-BY-NC-4.0';

export function useSTACForm(
  stacMetadata: STACMetadata | null
): UseSTACFormReturn {
  const [formState, setFormState] = useState<FormState>({
    sciDoi: '',
    sciCitation: '',
    license: DEFAULT_LICENSE,
    customTitles: {},
  });

  // Initialize form fields from existing metadata
  useEffect(() => {
    if (stacMetadata?.collection) {
      setFormState((prev) => {
        // Get server values
        const serverSciDoi = stacMetadata.collection['sci:doi'] || '';
        const serverSciCitation = stacMetadata.collection['sci:citation'] || '';
        const serverLicense =
          (stacMetadata.collection as any).license || DEFAULT_LICENSE;

        // Preserve user input if it differs from server data
        // This prevents form values from reverting after submission
        const finalSciDoi =
          prev.sciDoi && prev.sciDoi !== serverSciDoi
            ? prev.sciDoi
            : serverSciDoi;
        const finalSciCitation =
          prev.sciCitation && prev.sciCitation !== serverSciCitation
            ? prev.sciCitation
            : serverSciCitation;
        const finalLicense =
          prev.license && prev.license !== serverLicense
            ? prev.license
            : serverLicense;

        return {
          ...prev,
          sciDoi: finalSciDoi,
          sciCitation: finalSciCitation,
          license: finalLicense,
        };
      });
    }

    // Initialize custom titles from STAC items
    if (stacMetadata?.items) {
      const existingTitles: Record<string, string> = {};
      const defaultTitlePattern = /^\d{4}-\d{2}-\d{2}_[\w\s]+_[\w\s]+_[\w\s]+$/;

      stacMetadata.items.forEach((item) => {
        if ('properties' in item && item.properties?.title) {
          // Only include non-default titles
          if (!defaultTitlePattern.test(item.properties.title)) {
            existingTitles[item.id] = item.properties.title;
          }
        }
      });

      setFormState((prev) => {
        // Merge user input with server data on a per-item basis
        // For each item, prefer user input if it exists and differs from server data
        const mergedCustomTitles: Record<string, string> = {
          ...existingTitles,
        };

        // Preserve user input for items that haven't been synced to server yet
        Object.keys(prev.customTitles).forEach((itemId) => {
          const userTitle = prev.customTitles[itemId];
          const serverTitle = existingTitles[itemId];

          // Keep user input if:
          // 1. Server doesn't have this title yet, OR
          // 2. User has modified it since the last server sync
          if (!serverTitle || userTitle !== serverTitle) {
            mergedCustomTitles[itemId] = userTitle;
          }
        });

        return {
          ...prev,
          customTitles: mergedCustomTitles,
        };
      });
    }
  }, [stacMetadata]);

  const updateFormField = <K extends keyof FormState>(
    field: K,
    value: FormState[K]
  ) => {
    setFormState((prev) => ({ ...prev, [field]: value }));
  };

  const buildRequestPayload = (): STACRequestPayload => {
    const payload: STACRequestPayload = {};

    if (formState.sciDoi) payload.sci_doi = formState.sciDoi;
    if (formState.sciCitation) payload.sci_citation = formState.sciCitation;
    if (formState.license) payload.license = formState.license;
    if (Object.keys(formState.customTitles).length > 0) {
      payload.custom_titles = formState.customTitles;
    }

    return payload;
  };

  const resetForm = () => {
    setFormState({
      sciDoi: '',
      sciCitation: '',
      license: DEFAULT_LICENSE,
      customTitles: {},
    });
  };

  return {
    formState,
    updateFormField,
    buildRequestPayload,
    resetForm,
  };
}

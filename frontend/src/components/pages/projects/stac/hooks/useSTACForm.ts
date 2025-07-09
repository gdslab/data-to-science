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
      setFormState((prev) => ({
        ...prev,
        sciDoi: stacMetadata.collection['sci:doi'] || '',
        sciCitation: stacMetadata.collection['sci:citation'] || '',
        license: (stacMetadata.collection as any).license || DEFAULT_LICENSE,
      }));
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

      setFormState((prev) => ({ ...prev, customTitles: existingTitles }));
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

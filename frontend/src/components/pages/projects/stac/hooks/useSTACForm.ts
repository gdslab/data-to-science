import { useState, useEffect } from 'react';
import { STACMetadata, STACRequestPayload } from '../STACTypes';
import { Project } from '../../Project';

interface FormState {
  contactName: string;
  contactEmail: string;
  sciDoi: string;
  sciCitation: string;
  license: string;
  customTitles: Record<string, string>;
  includeRawDataLinks: Set<string>;
}

interface UseSTACFormReturn {
  formState: FormState;
  updateFormField: <K extends keyof FormState>(
    field: K,
    value: FormState[K]
  ) => void;
  buildRequestPayload: () => STACRequestPayload;
  resetForm: () => void;
  toggleRawDataLink: (itemId: string) => void;
  toggleAllRawDataLinks: (allSuccessfulItemIds: string[]) => void;
}

const DEFAULT_LICENSE = 'CC-BY-NC-4.0';

export function useSTACForm(
  stacMetadata: STACMetadata | null,
  project: Project
): UseSTACFormReturn {
  const [formState, setFormState] = useState<FormState>({
    contactName: '',
    contactEmail: '',
    sciDoi: '',
    sciCitation: '',
    license: DEFAULT_LICENSE,
    customTitles: {},
    includeRawDataLinks: new Set(),
  });

  // Initialize form fields from existing metadata
  useEffect(() => {
    if (stacMetadata?.collection) {
      setFormState((prev) => {
        // Get server values for scientific metadata
        const serverSciDoi = stacMetadata.collection['sci:doi'] || '';
        const serverSciCitation = stacMetadata.collection['sci:citation'] || '';
        const serverLicense =
          (stacMetadata.collection as any).license || DEFAULT_LICENSE;

        // Get server values for contact metadata
        let serverContactName = '';
        let serverContactEmail = '';
        const contacts = (stacMetadata.collection as any).contacts;
        if (contacts && Array.isArray(contacts) && contacts.length > 0) {
          const contact = contacts[0];
          serverContactName = contact.name || '';
          if (contact.emails && Array.isArray(contact.emails) && contact.emails.length > 0) {
            serverContactEmail = contact.emails[0].value || '';
          }
        }

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

        // For contact fields, only use cached values if they exist
        // Preserve user input if it differs from server data
        const finalContactName =
          prev.contactName && prev.contactName !== serverContactName
            ? prev.contactName
            : serverContactName;
        const finalContactEmail =
          prev.contactEmail && prev.contactEmail !== serverContactEmail
            ? prev.contactEmail
            : serverContactEmail;

        return {
          ...prev,
          sciDoi: finalSciDoi,
          sciCitation: finalSciCitation,
          license: finalLicense,
          contactName: finalContactName,
          contactEmail: finalContactEmail,
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

    // Initialize raw data link selections from STAC items
    if (stacMetadata?.items) {
      const itemsWithRawDataLinks = new Set<string>();

      stacMetadata.items.forEach((item) => {
        // Check if this is a successful item (has links property)
        if ('links' in item && item.links) {
          // Check if this item has a derived_from link (indicates raw data link was previously selected)
          const hasDerivedFromLink = item.links.some(
            (link) => link.rel === 'derived_from'
          );
          if (hasDerivedFromLink) {
            itemsWithRawDataLinks.add(item.id);
          }
        }
      });

      setFormState((prev) => {
        // Merge server data with any user selections not yet saved
        // This preserves user input while respecting server state
        const mergedSet = new Set([
          ...itemsWithRawDataLinks,
          ...prev.includeRawDataLinks,
        ]);

        return {
          ...prev,
          includeRawDataLinks: mergedSet,
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

    // Add contact fields if both are present
    if (formState.contactName && formState.contactEmail) {
      payload.contact_name = formState.contactName;
      payload.contact_email = formState.contactEmail;
    }

    if (formState.sciDoi) payload.sci_doi = formState.sciDoi;
    if (formState.sciCitation) payload.sci_citation = formState.sciCitation;
    if (formState.license) payload.license = formState.license;
    if (Object.keys(formState.customTitles).length > 0) {
      payload.custom_titles = formState.customTitles;
    }
    if (formState.includeRawDataLinks.size > 0) {
      payload.include_raw_data_links = Array.from(formState.includeRawDataLinks);
    }

    return payload;
  };

  const resetForm = () => {
    setFormState({
      contactName: '',
      contactEmail: '',
      sciDoi: '',
      sciCitation: '',
      license: DEFAULT_LICENSE,
      customTitles: {},
      includeRawDataLinks: new Set(),
    });
  };

  const toggleRawDataLink = (itemId: string) => {
    setFormState((prev) => {
      const newSet = new Set(prev.includeRawDataLinks);
      if (newSet.has(itemId)) {
        newSet.delete(itemId);
      } else {
        newSet.add(itemId);
      }
      return { ...prev, includeRawDataLinks: newSet };
    });
  };

  const toggleAllRawDataLinks = (allSuccessfulItemIds: string[]) => {
    setFormState((prev) => {
      // Check if all successful items are currently checked
      const allChecked = allSuccessfulItemIds.every((id) =>
        prev.includeRawDataLinks.has(id)
      );

      // If all checked, uncheck all. Otherwise, check all.
      const newSet = allChecked
        ? new Set<string>()
        : new Set(allSuccessfulItemIds);

      return { ...prev, includeRawDataLinks: newSet };
    });
  };

  return {
    formState,
    updateFormField,
    buildRequestPayload,
    resetForm,
    toggleRawDataLink,
    toggleAllRawDataLinks,
  };
}

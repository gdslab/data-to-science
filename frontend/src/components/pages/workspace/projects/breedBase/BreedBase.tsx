import { useEffect } from 'react';
import { useForm, FormProvider, SubmitHandler } from 'react-hook-form';
import { useParams } from 'react-router';
import { yupResolver } from '@hookform/resolvers/yup';

import BreedBaseStudies from './BreedBaseStudies';
import BreedBaseStudiesTable from './BreedBaseStudiesTable';
import { TextInput } from '../../../../RHFInputs';
import { useBreedBase } from './useBreedBase';
import { BreedBaseFormData } from './BreedBase.types';

import defaultValues from './defaultValues';
import validationSchema from './validationSchema';

export default function BreedBase() {
  const { projectId } = useParams();

  const methods = useForm<BreedBaseFormData>({
    defaultValues,
    resolver: yupResolver(validationSchema),
  });

  const {
    error,
    isLoading,
    breedbaseStudies,
    studiesApiResponse,
    studyDetails,
    loadingStudyDetails,
    fetchBreedbaseStudies,
    searchStudies,
    removeStudy,
    fetchPage,
    addStudy,
    fetchStudyDetails,
  } = useBreedBase({ projectId: projectId!, methods });

  useEffect(() => {
    fetchBreedbaseStudies();
  }, [fetchBreedbaseStudies]);

  // Fetch study details when breedbaseStudies change
  useEffect(() => {
    breedbaseStudies.forEach((study) => {
      fetchStudyDetails(study.base_url, study.study_id);
    });
  }, [breedbaseStudies, fetchStudyDetails]);

  // Set default breedbaseUrl based on existing studies
  useEffect(() => {
    if (breedbaseStudies.length > 0) {
      // Count frequency of each base_url
      const urlCounts = breedbaseStudies.reduce((acc, study) => {
        acc[study.base_url] = (acc[study.base_url] || 0) + 1;
        return acc;
      }, {} as Record<string, number>);

      // Find the most common base_url (or first one in case of tie)
      const mostCommonUrl = Object.entries(urlCounts).reduce((a, b) =>
        a[1] >= b[1] ? a : b
      )[0];

      // Only set if the field is currently empty
      const currentValue = methods.getValues('breedbaseUrl');
      if (!currentValue) {
        methods.setValue('breedbaseUrl', mostCommonUrl);
      }
    }
  }, [breedbaseStudies, methods]);

  const { handleSubmit } = methods;

  const onSubmit: SubmitHandler<BreedBaseFormData> = async (data) => {
    await searchStudies(data);
  };

  return (
    <div className="h-full flex flex-col gap-4">
      <h2>BreedBase Connection</h2>
      <div className="flex flex-col gap-2">
        <div className="flex flex-col">
          <h3>Studies</h3>
          <p className="text-sm text-gray-500">
            Studies associated with this project.
          </p>
        </div>
        <BreedBaseStudiesTable
          studies={breedbaseStudies}
          studyDetails={studyDetails}
          loadingStudyDetails={loadingStudyDetails}
          onRemoveStudy={removeStudy}
        />
      </div>
      <hr className="border-t border-gray-400" />
      <FormProvider {...methods}>
        <form onSubmit={handleSubmit(onSubmit)} className="mb-4">
          <div className="flex flex-col">
            <h3>Search for studies</h3>
            <p className="text-sm text-gray-500">
              Search for studies to add to this project.
            </p>
          </div>
          <div className="flex flex-col gap-8">
            <TextInput
              fieldName="breedbaseUrl"
              label="BreedBase URL"
              placeholder="https://server/brapi/version"
            />
            <fieldset>
              <legend>Search Parameters (optional)</legend>
              <p className="text-sm text-gray-500">
                Separate multiple values with semicolons.
              </p>
              <div className="flex gap-2">
                <TextInput
                  fieldName="studyDbIds"
                  label="Study DB IDs"
                  placeholder="cf6c4bd4;691e69d6"
                />
                <TextInput
                  fieldName="studyNames"
                  label="Study Names"
                  placeholder="The First Bob Study 2017;Wheat Yield Trial 246"
                />
                <TextInput
                  fieldName="programNames"
                  label="Program Name"
                  placeholder="The First Bob Study 2017;Wheat Yield Trial 246"
                />
                <TextInput
                  fieldName="year"
                  label="Program Year"
                  placeholder="2017;2018;2019"
                />
              </div>
            </fieldset>
            {error && <div className="text-red-500 text-sm">{error}</div>}
            <div>
              <button
                className="w-32 bg-accent2/90 text-white font-semibold py-1 rounded-sm enabled:hover:bg-accent2 disabled:opacity-75 disabled:cursor-not-allowed"
                type="submit"
                disabled={isLoading}
              >
                {isLoading ? 'Searching...' : 'Search Studies'}
              </button>
            </div>
          </div>
        </form>
      </FormProvider>
      {studiesApiResponse && (
        <BreedBaseStudies
          data={studiesApiResponse}
          onAddStudyId={addStudy}
          onPageChange={fetchPage}
        />
      )}
    </div>
  );
}

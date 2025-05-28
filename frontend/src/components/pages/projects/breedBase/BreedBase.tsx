import { useEffect } from 'react';
import { useForm, FormProvider, SubmitHandler } from 'react-hook-form';
import { useParams } from 'react-router-dom';
import { yupResolver } from '@hookform/resolvers/yup';
import { XCircleIcon } from '@heroicons/react/24/solid';

import BreedBaseStudies from './BreedBaseStudies';
import { TextInput } from '../../../RHFInputs';
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
    fetchBreedbaseStudies,
    searchStudies,
    removeStudy,
    fetchPage,
    addStudy,
  } = useBreedBase({ projectId: projectId!, methods });

  useEffect(() => {
    fetchBreedbaseStudies();
  }, []);

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
        {breedbaseStudies.length > 0 ? (
          <>
            <div className="max-w-xl grid grid-cols-[1fr_auto_auto] items-center gap-4 p-2 text-sm font-medium text-gray-500 border-b border-gray-200">
              <div className="truncate">Base URL</div>
              <div className="px-2">Study ID</div>
              <div className="w-5 flex justify-center">Remove</div>
            </div>
            {breedbaseStudies.map((study) => (
              <div
                key={study.id}
                className="max-w-xl grid grid-cols-[1fr_auto_auto] items-center gap-4 p-2 hover:bg-gray-50 rounded"
              >
                <div className="text-gray-700 truncate" title={study.base_url}>
                  {study.base_url}
                </div>
                <div className="text-gray-700 px-2" title={study.study_id}>
                  {study.study_id}
                </div>
                <div className="w-5 flex justify-center">
                  <button
                    className="text-red-500 hover:text-red-700 transition-colors flex-shrink-0"
                    onClick={() => removeStudy(study.id)}
                    title="Remove connection"
                  >
                    <XCircleIcon className="h-5 w-5" />
                  </button>
                </div>
              </div>
            ))}
          </>
        ) : (
          <div>No studies found</div>
        )}
      </div>
      <hr className="border-t border-gray-400" />
      <FormProvider {...methods}>
        <form onSubmit={handleSubmit(onSubmit)}>
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
              </div>
            </fieldset>
            {error && <div className="text-red-500 text-sm">{error}</div>}
            <div>
              <button
                className="w-32 bg-accent2/90 text-white font-semibold py-1 rounded enabled:hover:bg-accent2 disabled:opacity-75 disabled:cursor-not-allowed"
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

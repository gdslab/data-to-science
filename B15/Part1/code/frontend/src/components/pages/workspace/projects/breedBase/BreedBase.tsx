import { useEffect } from 'react';
import { useForm, FormProvider, SubmitHandler } from 'react-hook-form';
import { useParams } from 'react-router';
import { yupResolver } from '@hookform/resolvers/yup';

import BreedBaseStudies from './BreedBaseStudies';
import BreedBaseStudiesTable from './BreedBaseStudiesTable';
import { TextInput } from '../../../../RHFInputs';
import { useBreedBase } from './useBreedBase';
import { useBreedBaseOAuth } from './useBreedBaseOAuth';
import { BreedBaseFormData } from './BreedBase.types';

import defaultValues from './defaultValues';
import validationSchema from './validationSchema';

export default function BreedBase() {
  const { projectId } = useParams();

  const methods = useForm<BreedBaseFormData>({
    defaultValues,
    resolver: yupResolver(validationSchema),
  });

  const watchedUrl = methods.watch('breedbaseUrl');

  const {
    authStatus,
    popupBlocked,
    requiresOAuth,
    startOAuth,
    getToken,
    getAuthorizeUrl,
    checkAuth,
    expireAuth,
  } = useBreedBaseOAuth();

  const needsOAuth = watchedUrl ? requiresOAuth(watchedUrl) : false;
  const oAuthReady = !needsOAuth || authStatus === 'authenticated';

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
    refreshStudyDetails,
  } = useBreedBase({ projectId: projectId!, methods, getAuthToken: getToken, onAuthExpired: expireAuth });

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

  // Refresh study details after re-authentication
  useEffect(() => {
    if (authStatus === 'authenticated' && breedbaseStudies.length > 0) {
      refreshStudyDetails();
    }
  }, [authStatus, breedbaseStudies.length, refreshStudyDetails]);

  // Check auth status when URL changes
  useEffect(() => {
    if (watchedUrl && requiresOAuth(watchedUrl)) {
      checkAuth(watchedUrl);
    }
  }, [watchedUrl, checkAuth, requiresOAuth]);

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
            {needsOAuth && (
              <div className="flex items-center gap-3 p-3 bg-amber-50 border border-amber-200 rounded">
                {authStatus === 'authenticated' ? (
                  <span className="text-green-700 text-sm font-medium">
                    Authenticated with{' '}
                    {(() => {
                      try {
                        return new URL(watchedUrl).hostname;
                      } catch {
                        return 'server';
                      }
                    })()}
                  </span>
                ) : (
                  <>
                    <span className="text-sm text-gray-700">
                      {authStatus === 'expired'
                        ? 'Session expired. Please log in again.'
                        : 'Authentication required for this server.'}
                    </span>
                    <button
                      type="button"
                      onClick={() => startOAuth(watchedUrl)}
                      className="bg-accent2/90 text-white font-semibold px-3 py-1 rounded-sm hover:bg-accent2"
                    >
                      Log in
                    </button>
                  </>
                )}
                {popupBlocked && (
                  <p className="text-sm text-red-600">
                    Popup was blocked. Please allow popups or{' '}
                    <a
                      href={getAuthorizeUrl(watchedUrl)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="underline"
                    >
                      click here to log in
                    </a>
                    .
                  </p>
                )}
              </div>
            )}
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
                disabled={isLoading || !oAuthReady}
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
          existingStudyIds={breedbaseStudies.map((s) => s.study_id)}
          onAddStudyId={addStudy}
          onPageChange={fetchPage}
        />
      )}
    </div>
  );
}

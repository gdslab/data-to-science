import axios, { AxiosResponse, isAxiosError } from 'axios';
import { useEffect, useState } from 'react';
import { Link, Params, useLoaderData } from 'react-router-dom';
import { ArrowDownTrayIcon } from '@heroicons/react/24/outline';

import Alert, { Status } from '../../../Alert';
import {
  IndoorProjectAPIResponse,
  IndoorProjectDataAPIResponse,
  IndoorProjectDataSpreadsheetAPIResponse,
  IndoorProjectDataVizAPIResponse,
  IndoorProjectDataViz2APIResponse,
} from './IndoorProject';
import IndoorProjectUploadModal from './IndoorProjectUploadModal';
import IndoorProjectPageLayout from './IndoorProjectPageLayout';
import IndoorProjectDataVizGraph from './IndoorProjectDataVizGraph';
import IndoorProjectDataViz2Graph from './IndoorProjectDataViz2Graph';
import IndoorProjectDataVizForm, {
  fetchIndoorProjectVizData,
} from './IndoorProjectDataVizForm';
import IndoorProjectDataViz2Form from './IndoorProjectDataVizForm2';
import LoadingBars from '../../../LoadingBars';
import PotOverview from './PotOverview';

export async function loader({ params }: { params: Params<string> }) {
  try {
    const indoorProjectResponse: AxiosResponse<IndoorProjectAPIResponse> =
      await axios.get(
        `${import.meta.env.VITE_API_V1_STR}/indoor_projects/${
          params.indoorProjectId
        }`
      );
    if (indoorProjectResponse && indoorProjectResponse.status == 200) {
      return {
        indoorProject: indoorProjectResponse.data,
      };
    } else {
      throw new Response('Indoor project not found', { status: 404 });
    }
  } catch (err) {
    throw new Response('Indoor project not found', { status: 404 });
  }
}

export default function IndoorProjectDetail() {
  const [potOverviewData, setPotOverviewData] =
    useState<IndoorProjectDataVizAPIResponse | null>(null);
  const [indoorProjectData, setIndoorProjectData] = useState<
    IndoorProjectDataAPIResponse[]
  >([]);
  const [indoorProjectDataVizData, setIndoorProjectDataVizData] =
    useState<IndoorProjectDataVizAPIResponse | null>(null);
  const [indoorProjectDataViz2Data, setIndoorProjectDataViz2Data] =
    useState<IndoorProjectDataViz2APIResponse | null>(null);
  const [indoorProjectDataSpreadsheet, setIndoorProjectDataSpreadsheet] =
    useState<IndoorProjectDataSpreadsheetAPIResponse | null>(null);
  const { indoorProject } = useLoaderData() as {
    indoorProject: IndoorProjectAPIResponse;
  };
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState<Status | null>(null);

  console.log(indoorProjectDataSpreadsheet);

  useEffect(() => {
    const fetchIndoorProjectData = async (indoorProjectId: string) => {
      try {
        const response: AxiosResponse<IndoorProjectDataAPIResponse[]> =
          await axios.get(
            `${
              import.meta.env.VITE_API_V1_STR
            }/indoor_projects/${indoorProjectId}/uploaded`
          );
        setIndoorProjectData(response.data);
      } catch (error) {
        if (isAxiosError(error)) {
          // Axios-specific error handling
          const status = error.response?.status || 500;
          const message = error.response?.data?.message || error.message;

          throw {
            status,
            message: `Failed to load uploaded data: ${message}`,
          };
        } else {
          // Generic error handling
          throw {
            status: 500,
            message: 'An unexpected error occurred.',
          };
        }
      }
    };

    if (indoorProject) {
      fetchIndoorProjectData(indoorProject.id);
    }
  }, [indoorProject]);

  useEffect(() => {
    const fetchIndoorProjectSpreadsheet = async (
      indoorProjectId: string,
      indoorProjectDataId: string
    ) => {
      try {
        const response: AxiosResponse<IndoorProjectDataSpreadsheetAPIResponse> =
          await axios.get(
            `${
              import.meta.env.VITE_API_V1_STR
            }/indoor_projects/${indoorProjectId}/uploaded/${indoorProjectDataId}`
          );
        setIndoorProjectDataSpreadsheet({
          records: response.data.records,
          summary: { id: indoorProjectDataId, ...response.data.summary },
          numeric_columns: response.data.numeric_columns,
        });
      } catch (error) {
        if (isAxiosError(error)) {
          // Axios-specific error handling
          const status = error.response?.status || 500;
          const message = error.response?.data?.message || error.message;

          throw {
            status,
            message: `Failed to load spreadsheet data: ${message}`,
          };
        } else {
          // Generic error handling
          throw {
            status: 500,
            message: 'An unexpected error occurred.',
          };
        }
      }
    };

    if (indoorProject && indoorProjectData.length > 0) {
      const spreadsheets = indoorProjectData.filter(
        ({ file_type }) => file_type === '.xlsx'
      );
      if (spreadsheets.length > 0) {
        fetchIndoorProjectSpreadsheet(indoorProject.id, spreadsheets[0].id);
      }
    }
  }, [indoorProject, indoorProjectData]);

  useEffect(() => {
    let isMounted = true;

    async function loadVizData() {
      // Reset states at the start of each fetch
      setStatus(null);
      setIsLoading(true);
      setPotOverviewData(null);

      // Find the indoor project data id of the first spreadsheet
      const indoorProjectDataId = indoorProjectData.find(
        ({ file_type }) => file_type === '.xlsx'
      )?.id;

      // If no indoor project or indoor project data id, return early
      if (!indoorProject || !indoorProjectDataId) {
        setIsLoading(false);
        return;
      }

      try {
        const data = await fetchIndoorProjectVizData(
          indoorProject.id,
          indoorProjectDataId,
          'side',
          'single_pot'
        );

        // Check if component is still mounted before updating state
        if (isMounted) {
          setPotOverviewData(data);
        }
      } catch (error) {
        if (isMounted) {
          setStatus({
            type: 'error',
            msg:
              error instanceof Error
                ? error.message
                : 'Failed to load visualization data',
          });
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadVizData();

    // Cleanup function to prevent setting state on unmounted component
    return () => {
      isMounted = false;
    };
  }, [indoorProject, indoorProjectData, setPotOverviewData]);

  const formattedDate = (uploadedFile: IndoorProjectDataAPIResponse): string =>
    new Date(uploadedFile.upload_date).toLocaleDateString();

  if (!indoorProject)
    return (
      <div>
        <span>No indoor project found</span>
      </div>
    );

  return (
    <IndoorProjectPageLayout>
      <div className="flex flex-col sm:flex-row gap-4">
        {/* Left column */}
        <div className="w-full md:w-2/5 flex flex-col gap-8">
          <div className="flex flex-col gap-2">
            <h2 className="truncate" title={indoorProject.title}>
              {indoorProject.title}
            </h2>
            <p className="text-gray-600 line-clamp-3">
              {indoorProject.description}
            </p>
          </div>

          {indoorProjectData.length > 0 && (
            <div className="flex flex-col gap-2">
              <h3>Previously Uploaded Data</h3>
              <ul className="list-disc list-inside">
                {indoorProjectData.map((uploadedFile) => (
                  <li key={uploadedFile.id} className="flex items-center gap-2">
                    <span
                      className="truncate max-w-[200px]"
                      title={uploadedFile.original_filename}
                    >
                      {uploadedFile.original_filename}
                      {uploadedFile.file_type &&
                        ` (${uploadedFile.file_type.toUpperCase()})`}
                    </span>{' '}
                    <span className="italic text-gray-600">{`(Uploaded on ${formattedDate(
                      uploadedFile
                    )})`}</span>
                    <a href={uploadedFile.file_path} download>
                      <ArrowDownTrayIcon className="w-4 h-4" />
                      <span className="sr-only">Download</span>
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="w-48">
            <IndoorProjectUploadModal
              btnLabel="Add data"
              indoorProjectId={indoorProject.id}
            />
          </div>
        </div>
      </div>

      <div className="w-full flex flex-col gap-4">
        <span className="text-lg font-bold">
          Pots
          {indoorProjectDataSpreadsheet
            ? ` (${Object.keys(indoorProjectDataSpreadsheet.records).length})`
            : ''}
        </span>
        <span>
          Planting date:{' '}
          {indoorProjectDataSpreadsheet?.summary?.planting_date
            ? new Date(
                indoorProjectDataSpreadsheet.summary.planting_date
              ).toLocaleDateString()
            : 'Not available'}
        </span>
        {isLoading || !indoorProjectDataSpreadsheet || !potOverviewData ? (
          <LoadingBars />
        ) : (
          <div className="max-h-96 flex flex-wrap justify-start p-4 gap-4">
            <PotOverview
              data={potOverviewData}
              indoorProjectDataSpreadsheet={indoorProjectDataSpreadsheet}
              indoorProjectId={indoorProject.id}
            />
          </div>
        )}
      </div>
      {status && <Alert alertType={status.type}>{status.msg}</Alert>}

      <div className="border-b-2 border-gray-300" />

      <div className="py-4">
        <h3>Graphs</h3>
        <IndoorProjectDataVizForm
          indoorProjectId={indoorProject.id}
          indoorProjectDataId={
            indoorProjectData.find(({ file_type }) => file_type === '.xlsx')?.id
          }
          setIndoorProjectDataVizData={setIndoorProjectDataVizData}
        />
        {indoorProjectDataVizData && (
          <IndoorProjectDataVizGraph data={indoorProjectDataVizData} />
        )}
        {indoorProjectDataSpreadsheet && (
          <IndoorProjectDataViz2Form
            indoorProjectId={indoorProject.id}
            indoorProjectDataId={
              indoorProjectData.find(({ file_type }) => file_type === '.xlsx')
                ?.id
            }
            numericColumns={indoorProjectDataSpreadsheet.numeric_columns}
            setIndoorProjectDataViz2Data={setIndoorProjectDataViz2Data}
          />
        )}
        {indoorProjectDataViz2Data && (
          <IndoorProjectDataViz2Graph data={indoorProjectDataViz2Data} />
        )}
      </div>
    </IndoorProjectPageLayout>
  );
}

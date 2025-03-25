import axios, { AxiosResponse, isAxiosError } from 'axios';
import { useEffect, useState } from 'react';
import { Params, useLoaderData } from 'react-router-dom';
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
import LoadingBars from '../../../LoadingBars';

import PotModuleDataVisualization from './PotModule/PotModuleDataVisualization';
import { fetchPotGroupModuleVisualizationData } from './PotGroupModule/service';
import PotGroupModuleForm from './PotGroupModule/PotGroupModuleForm';
import PotGroupModuleDataVisualization from './PotGroupModule/PotGroupModuleDataVisualization';
import TraitModuleForm from './TraitModule/TraitModuleForm';
import TraitModuleDataVisualization from './TraitModule/TraitModuleDataVisualization';

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
  // Indoor project data from database
  const [indoorProjectData, setIndoorProjectData] = useState<
    IndoorProjectDataAPIResponse[]
  >([]);
  const [indoorProjectDataSpreadsheet, setIndoorProjectDataSpreadsheet] =
    useState<IndoorProjectDataSpreadsheetAPIResponse | null>(null);
  // Visualization data
  const [potModuleVisualizationData, setPotModuleVisualizationData] =
    useState<IndoorProjectDataVizAPIResponse | null>(null);
  const [potGroupModuleVisualizationData, setPotGroupModuleVisualizationData] =
    useState<IndoorProjectDataVizAPIResponse | null>(null);
  const [traitModuleVisualizationData, setTraitModuleVisualizationData] =
    useState<IndoorProjectDataViz2APIResponse | null>(null);
  const { indoorProject } = useLoaderData() as {
    indoorProject: IndoorProjectAPIResponse;
  };
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState<Status | null>(null);

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

  console.log(indoorProjectData);

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
      setPotModuleVisualizationData(null);

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
        const data = await fetchPotGroupModuleVisualizationData({
          indoorProjectId: indoorProject.id,
          indoorProjectDataId,
          cameraOrientation: 'side',
          groupBy: 'single_pot',
        });

        // Check if component is still mounted before updating state
        if (isMounted) {
          setPotModuleVisualizationData(data);
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
  }, [indoorProject, indoorProjectData, setPotModuleVisualizationData]);

  const formattedDate = (uploadedFile: IndoorProjectDataAPIResponse): string =>
    new Date(uploadedFile.upload_date).toLocaleDateString();

  const indoorProjectDataId = indoorProjectData.find(
    ({ file_type }) => file_type === '.xlsx'
  )?.id;

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
        {isLoading ||
        !indoorProjectDataSpreadsheet ||
        !potModuleVisualizationData ? (
          <LoadingBars />
        ) : (
          <div className="max-h-[450px] flex flex-wrap justify-start p-4 gap-4 overflow-auto">
            <PotModuleDataVisualization
              data={potModuleVisualizationData}
              indoorProjectDataSpreadsheet={indoorProjectDataSpreadsheet}
              indoorProjectId={indoorProject.id}
            />
          </div>
        )}
      </div>
      {status && <Alert alertType={status.type}>{status.msg}</Alert>}

      <div className="border-b-2 border-gray-300" />

      <div className="py-4">
        <h3>Visualizations</h3>
        {indoorProjectDataId && (
          <PotGroupModuleForm
            indoorProjectId={indoorProject.id}
            indoorProjectDataId={indoorProjectDataId}
            setVisualizationData={setPotGroupModuleVisualizationData}
          />
        )}
        {potGroupModuleVisualizationData && (
          <PotGroupModuleDataVisualization
            data={potGroupModuleVisualizationData}
          />
        )}
        {indoorProjectDataSpreadsheet && indoorProjectDataId && (
          <TraitModuleForm
            indoorProjectId={indoorProject.id}
            indoorProjectDataId={indoorProjectDataId}
            numericColumns={indoorProjectDataSpreadsheet.numeric_columns}
            setVisualizationData={setTraitModuleVisualizationData}
          />
        )}
        {traitModuleVisualizationData && (
          <TraitModuleDataVisualization data={traitModuleVisualizationData} />
        )}
      </div>
    </IndoorProjectPageLayout>
  );
}

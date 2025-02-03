import axios, { AxiosResponse, isAxiosError } from 'axios';
import { useEffect, useState } from 'react';
import { Link, Params, useLoaderData } from 'react-router-dom';

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
import IndoorProjectDataVizForm from './IndoorProjectDataVizForm';
import IndoorProjectDataViz2Form from './IndoorProjectDataVizForm2';

export async function loader({ params }: { params: Params<string> }) {
  try {
    const indoorProjectResponse: AxiosResponse<IndoorProjectAPIResponse> =
      await axios.get(
        `${import.meta.env.VITE_API_V1_STR}/indoor_projects/${params.indoorProjectId}`
      );
    if (indoorProjectResponse && indoorProjectResponse.status == 200) {
      console.log('indoor project api response:', indoorProjectResponse.data);
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
  const [showGraphs, setShowGraphs] = useState(false);
  const [showIndoorProjectDetails, setShowIndoorProjectDetails] = useState(false);
  const [showIndoorProjectPlants, setShowIndoorProjectPlants] = useState(false);
  const [showUploadedData, setShowUploadedData] = useState(false);

  const toggleIndoorProjectDetails = () =>
    setShowIndoorProjectDetails(!showIndoorProjectDetails);

  const toggleIndoorProjectPlants = () =>
    setShowIndoorProjectPlants(!showIndoorProjectPlants);

  const toggleShowUploadedData = () => setShowUploadedData(!showUploadedData);

  const toggleShowGraphs = () => setShowGraphs(!showGraphs);

  useEffect(() => {
    const fetchIndoorProjectData = async (indoorProjectId: string) => {
      try {
        const response: AxiosResponse<IndoorProjectDataAPIResponse[]> = await axios.get(
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

  function getRecord(key: string, attr: string): string {
    if (
      indoorProjectDataSpreadsheet &&
      indoorProjectDataSpreadsheet.records &&
      Number(key)
    ) {
      if (key in indoorProjectDataSpreadsheet.records) {
        return indoorProjectDataSpreadsheet.records[Number(key)][attr];
      }
    }
    return 'unknown';
  }

  console.log('indoorProjectDataSpreadsheet', indoorProjectDataSpreadsheet);

  if (!indoorProject)
    return (
      <div>
        <span>No indoor project found</span>
      </div>
    );

  return (
    <IndoorProjectPageLayout>
      <button
        type="button"
        onClick={toggleIndoorProjectDetails}
        className="px-4 py-2 bg-blue-500 text-white font-medium rounded hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-300"
      >
        {showIndoorProjectDetails
          ? 'Hide Indoor Project Details'
          : 'Show Indoor Project Details'}
      </button>
      {showIndoorProjectDetails && (
        <div>
          <h1>Indoor Project Details</h1>
          <pre className="whitespace-pre-wrap p-10 border-2 border-slate-600">
            {JSON.stringify(indoorProject, null, 2)}
          </pre>
        </div>
      )}
      <IndoorProjectUploadModal indoorProjectId={indoorProject.id} />
      <button
        type="button"
        onClick={toggleShowUploadedData}
        className="px-4 py-2 bg-blue-500 text-white font-medium rounded hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-300"
      >
        {showUploadedData ? 'Hide Uploaded Data' : 'Show Uploaded Data'}
      </button>
      {showUploadedData && (
        <div>
          <h2>Uploaded Data:</h2>
          <pre className="whitespace-pre-wrap p-10 border-2 border-slate-600 h-60 overflow-y-auto">
            {JSON.stringify(indoorProjectData, null, 2)}
          </pre>
        </div>
      )}
      {/* <h3>Spreadsheet Summary:</h3>
      {indoorProjectDataSpreadsheet && indoorProjectDataSpreadsheet.summary && (
        <pre className="whitespace-pre-wrap p-10 border-2 border-slate-600">
          {JSON.stringify(indoorProjectDataSpreadsheet.summary, null, 2)}
        </pre>
      )} */}
      <button
        type="button"
        onClick={toggleIndoorProjectPlants}
        className="px-4 py-2 bg-blue-500 text-white font-medium rounded hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-300"
      >
        {showIndoorProjectPlants ? 'Hide Plants' : 'Show Plants'}
      </button>
      {showIndoorProjectPlants && (
        <div>
          <h3>Plants:</h3>
          {indoorProjectDataSpreadsheet && (
            <div className="grid grid-cols-4 gap-4">
              {Object.keys(indoorProjectDataSpreadsheet.records).map((key) => (
                <Link
                  key={key}
                  to={`/indoor_projects/${indoorProject.id}/uploaded/${indoorProjectDataSpreadsheet.summary.id}/plants/${key}`}
                >
                  <div className="p-4 flex flex-col gap-2 border-2 border-slate-600 bg-white shadow-md hover:shadow-lg text-center">
                    <span className="font-bold">{key}</span>
                    <div className="flex flex-col justify-between">
                      <div className="flex justify-between">
                        <span>Species name:</span>
                        <span>{getRecord(key, 'species_name')}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Treatment:</span>
                        <span>{getRecord(key, 'treatment')}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Planting date:</span>
                        <span>{getRecord(key, 'planting_date').split('T')[0]}</span>
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      )}
      <button
        type="button"
        onClick={toggleShowGraphs}
        className="px-4 py-2 bg-blue-500 text-white font-medium rounded hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-300"
      >
        {showGraphs ? 'Hide Graphs' : 'Show Graphs'}
      </button>
      {showGraphs && (
        <div>
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
                indoorProjectData.find(({ file_type }) => file_type === '.xlsx')?.id
              }
              numericColumns={indoorProjectDataSpreadsheet.numeric_columns}
              setIndoorProjectDataViz2Data={setIndoorProjectDataViz2Data}
            />
          )}
          {indoorProjectDataViz2Data && (
            <IndoorProjectDataViz2Graph data={indoorProjectDataViz2Data} />
          )}
        </div>
      )}
    </IndoorProjectPageLayout>
  );
}

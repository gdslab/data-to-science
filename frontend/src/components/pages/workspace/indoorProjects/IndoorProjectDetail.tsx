import axios, { AxiosResponse } from 'axios';
import { useEffect, useState } from 'react';
import { Link, Params, useLoaderData } from 'react-router-dom';

import {
  IndoorProject,
  IndoorProjectAPIResponse,
  IndoorProjectDataAPIResponse,
  IndoorProjectDataSpreadsheetAPIResponse,
} from './IndoorProject';
import IndoorProjectDataVizForm from './IndoorProjectDataVizForm';
import IndoorProjectUploadModal from './IndoorProjectUploadModal';
import IndoorProjectPageLayout from './IndoorProjectPageLayout';

export async function loader({ params }: { params: Params<string> }) {
  try {
    const indoorProjectResponse: AxiosResponse<IndoorProjectAPIResponse> =
      await axios.get(
        `${import.meta.env.VITE_API_V1_STR}/indoor_projects/${params.indoorProjectId}`
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
  const [indoorProjectData, setIndoorProjectData] = useState<
    IndoorProjectDataAPIResponse[]
  >([]);
  const [indoorProjectDataSpreadsheet, setIndoorProjectDataSpreadsheet] =
    useState<IndoorProjectDataSpreadsheetAPIResponse | null>(null);
  const { indoorProject } = useLoaderData() as {
    indoorProject: IndoorProject;
  };

  useEffect(() => {
    const fetchIndoorProjectData = async (indoorProjectId: string) => {
      try {
        const response: AxiosResponse<IndoorProjectDataAPIResponse[]> = await axios.get(
          `${
            import.meta.env.VITE_API_V1_STR
          }/indoor_projects/${indoorProjectId}/uploaded`
        );
        if (response.status === 200) {
          setIndoorProjectData(response.data);
        } else {
          // log error
        }
      } catch (err) {
        // log error
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
        if (response.status === 200) {
          setIndoorProjectDataSpreadsheet({
            records: response.data.records,
            summary: { id: indoorProjectDataId, ...response.data.summary },
          });
        } else {
          // log error
        }
      } catch (err) {
        // log error
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

  if (!indoorProject)
    return (
      <div>
        <span>No indoor project found</span>
      </div>
    );

  console.log(indoorProjectDataSpreadsheet);
  console.log(indoorProjectData);
  return (
    <IndoorProjectPageLayout>
      <h1>Indoor Project Details</h1>
      <pre className="whitespace-pre-wrap p-10 border-2 border-slate-600">
        {JSON.stringify(indoorProject, null, 2)}
      </pre>
      <IndoorProjectUploadModal indoorProjectId={indoorProject.id} />
      {/* <h2>Uploaded Data:</h2>
      <pre className="whitespace-pre-wrap p-10 border-2 border-slate-600 h-60 overflow-y-auto">
        {JSON.stringify(indoorProjectData, null, 2)}
      </pre> */}
      <h3>Spreadsheet Summary:</h3>
      {indoorProjectDataSpreadsheet && indoorProjectDataSpreadsheet.summary && (
        <pre className="whitespace-pre-wrap p-10 border-2 border-slate-600">
          {JSON.stringify(indoorProjectDataSpreadsheet.summary, null, 2)}
        </pre>
      )}
      <IndoorProjectDataVizForm />
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
    </IndoorProjectPageLayout>
  );
}

import axios, { AxiosResponse } from 'axios';
import { Params, useLoaderData } from 'react-router-dom';

import Alert from '../../../Alert';
import { IndoorProjectAPIResponse } from './IndoorProject.d';
import IndoorProjectPageLayout from './IndoorProjectPageLayout';
import LoadingBars from '../../../LoadingBars';

import PotModuleDataVisualization from './PotModule/PotModuleDataVisualization';
import PotGroupModuleForm from './PotGroupModule/PotGroupModuleForm';
import PotGroupModuleDataVisualization from './PotGroupModule/PotGroupModuleDataVisualization';
import TraitModuleForm from './TraitModule/TraitModuleForm';
import TraitModuleDataVisualization from './TraitModule/TraitModuleDataVisualization';
import { useIndoorProjectData } from './hooks/useIndoorProjectData';
import IndoorProjectUploadForm from './IndoorProjectUploadForm';

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
  const { indoorProject } = useLoaderData() as {
    indoorProject: IndoorProjectAPIResponse;
  };
  const {
    indoorProjectData,
    indoorProjectDataSpreadsheet,
    potModuleVisualizationData,
    potGroupModuleVisualizationData,
    traitModuleVisualizationData,
    isLoading,
    error,
    setPotGroupModuleVisualizationData,
    setTraitModuleVisualizationData,
    refetch,
  } = useIndoorProjectData({ indoorProjectId: indoorProject.id });
  const indoorProjectDataId = indoorProjectData.find(
    ({ file_type }) => file_type === '.xlsx'
  )?.id;
  if (!indoorProject)
    return (
      <div>
        <span>No indoor project found</span>
      </div>
    );

  console.log('isLoading', isLoading);
  console.log('indoorProjectData', indoorProjectData);

  return (
    <IndoorProjectPageLayout>
      <div className="flex flex-col gap-4 h-full">
        {/* Project title and description */}
        <div className="flex flex-col gap-2 flex-shrink-0">
          <h2 className="truncate" title={indoorProject.title}>
            {indoorProject.title}
          </h2>
          <p className="text-gray-600 line-clamp-3">
            {indoorProject.description}
          </p>
          <hr className="my-4 border-gray-700" />
        </div>

        <div className="flex flex-col lg:flex-row gap-4 flex-1 min-h-0">
          {/* Upload form */}
          <div className="flex flex-col w-full lg:w-1/3 gap-8 p-4 border-b lg:border-b-0 lg:border-r border-gray-700 h-auto lg:h-full">
            <IndoorProjectUploadForm
              indoorProjectId={indoorProject.id}
              indoorProjectData={indoorProjectData}
              indoorProjectDataSpreadsheet={
                indoorProjectDataSpreadsheet || undefined
              }
              onUploadSuccess={refetch}
            />
          </div>
          {/* Data visualization */}
          <div className="flex flex-col w-full lg:w-2/3 gap-8 p-4 h-auto lg:h-full">
            {isLoading && <LoadingBars />}

            {!isLoading && indoorProjectData.length === 0 && (
              <div className="flex flex-col justify-center items-center h-full">
                <h3>No data yet</h3>
                <p className="text-gray-400">
                  Please upload data files to get started
                </p>
              </div>
            )}

            {!isLoading && indoorProjectData.length > 0 && (
              <div className="w-full flex flex-col gap-4">
                <span className="text-lg font-bold">
                  Pots
                  {indoorProjectDataSpreadsheet
                    ? ` (${
                        Object.keys(indoorProjectDataSpreadsheet.records).length
                      })`
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

                {indoorProjectDataSpreadsheet && potModuleVisualizationData && (
                  <div className="max-h-[450px] flex flex-wrap justify-start p-4 gap-4 overflow-auto">
                    <PotModuleDataVisualization
                      data={potModuleVisualizationData}
                      indoorProjectDataSpreadsheet={
                        indoorProjectDataSpreadsheet
                      }
                      indoorProjectId={indoorProject.id}
                    />
                  </div>
                )}

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
                    numericColumns={
                      indoorProjectDataSpreadsheet.numeric_columns
                    }
                    setVisualizationData={setTraitModuleVisualizationData}
                  />
                )}
                {traitModuleVisualizationData && (
                  <TraitModuleDataVisualization
                    data={traitModuleVisualizationData}
                  />
                )}
              </div>
            )}

            {error && <Alert alertType="error">{error.message}</Alert>}
          </div>
        </div>
      </div>
    </IndoorProjectPageLayout>
  );
}

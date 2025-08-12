import { AxiosResponse } from 'axios';
import { Params, useLoaderData } from 'react-router-dom';
import { Tab } from '@headlessui/react';

import api from '../../../../api';
import Alert from '../../../Alert';
import { IndoorProjectAPIResponse } from './IndoorProject.d';
import IndoorProjectPageLayout from './IndoorProjectPageLayout';
import LoadingBars from '../../../LoadingBars';

import PotModuleDataVisualization from './PotModule/PotModuleDataVisualization';
import PotGroupModuleForm from './PotGroupModule/PotGroupModuleForm';
import PotGroupModuleDataVisualization from './PotGroupModule/PotGroupModuleDataVisualization';
import TraitModuleForm from './TraitModule/TraitModuleForm';
import TraitModuleDataVisualization from './TraitModule/TraitModuleDataVisualization';
import TraitScatterModuleForm from './TraitModule/TraitScatterModuleForm';
import TraitScatterModuleDataVisualization from './TraitModule/TraitScatterModuleDataVisualization';
import { useIndoorProjectData } from './hooks/useIndoorProjectData';
import IndoorProjectUploadForm from './IndoorProjectUploadForm';

export async function loader({ params }: { params: Params<string> }) {
  try {
    const indoorProjectResponse: AxiosResponse<IndoorProjectAPIResponse> =
      await api.get(
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
    traitScatterModuleVisualizationData,
    isLoading,
    error,
    setPotGroupModuleVisualizationData,
    setTraitModuleVisualizationData,
    setTraitScatterModuleVisualizationData,
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

                <Tab.Group>
                  <Tab.List className="flex space-x-1 rounded-xl bg-gray-800 p-1">
                    <Tab
                      className={({ selected }) =>
                        `w-full rounded-lg py-2.5 px-3 text-sm font-medium leading-5 text-white transition-all duration-150 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 ${
                          selected
                            ? 'bg-blue-600 shadow'
                            : 'text-gray-400 hover:bg-gray-700 hover:text-white'
                        }`
                      }
                    >
                      Pot Overview
                    </Tab>
                    <Tab
                      className={({ selected }) =>
                        `w-full rounded-lg py-2.5 px-3 text-sm font-medium leading-5 text-white transition-all duration-150 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 ${
                          selected
                            ? 'bg-blue-600 shadow'
                            : 'text-gray-400 hover:bg-gray-700 hover:text-white'
                        }`
                      }
                    >
                      Pot Groups
                    </Tab>
                    <Tab
                      className={({ selected }) =>
                        `w-full rounded-lg py-2.5 px-3 text-sm font-medium leading-5 text-white transition-all duration-150 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 ${
                          selected
                            ? 'bg-blue-600 shadow'
                            : 'text-gray-400 hover:bg-gray-700 hover:text-white'
                        }`
                      }
                    >
                      Traits
                    </Tab>
                    <Tab
                      className={({ selected }) =>
                        `w-full rounded-lg py-2.5 px-3 text-sm font-medium leading-5 text-white transition-all duration-150 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 ${
                          selected
                            ? 'bg-blue-600 shadow'
                            : 'text-gray-400 hover:bg-gray-700 hover:text-white'
                        }`
                      }
                    >
                      Trait Scatter
                    </Tab>
                  </Tab.List>
                  <Tab.Panels className="mt-4">
                    <Tab.Panel className="rounded-xl bg-gray-50 p-4 focus:outline-none">
                      {indoorProjectDataSpreadsheet &&
                        potModuleVisualizationData && (
                          <div className="max-h-[450px] flex flex-wrap justify-start gap-4 overflow-auto">
                            <PotModuleDataVisualization
                              data={potModuleVisualizationData}
                              indoorProjectDataSpreadsheet={
                                indoorProjectDataSpreadsheet
                              }
                              indoorProjectId={indoorProject.id}
                            />
                          </div>
                        )}
                    </Tab.Panel>
                    <Tab.Panel className="rounded-xl bg-gray-50 p-4 focus:outline-none">
                      {indoorProjectDataId && (
                        <PotGroupModuleForm
                          indoorProjectId={indoorProject.id}
                          indoorProjectDataId={indoorProjectDataId}
                          setVisualizationData={
                            setPotGroupModuleVisualizationData
                          }
                        />
                      )}
                      {potGroupModuleVisualizationData && (
                        <div className="mt-4">
                          <PotGroupModuleDataVisualization
                            data={potGroupModuleVisualizationData}
                          />
                        </div>
                      )}
                    </Tab.Panel>
                    <Tab.Panel className="rounded-xl bg-gray-50 p-4 focus:outline-none">
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
                        <div className="mt-4">
                          <TraitModuleDataVisualization
                            data={traitModuleVisualizationData}
                          />
                        </div>
                      )}
                    </Tab.Panel>
                    <Tab.Panel className="rounded-xl bg-gray-50 p-4 focus:outline-none">
                      {indoorProjectDataSpreadsheet && indoorProjectDataId && (
                        <TraitScatterModuleForm
                          indoorProjectId={indoorProject.id}
                          indoorProjectDataId={indoorProjectDataId}
                          numericColumns={
                            indoorProjectDataSpreadsheet.numeric_columns
                          }
                          setVisualizationData={
                            setTraitScatterModuleVisualizationData
                          }
                        />
                      )}
                      {traitScatterModuleVisualizationData && (
                        <div className="mt-4">
                          <TraitScatterModuleDataVisualization
                            data={traitScatterModuleVisualizationData}
                          />
                        </div>
                      )}
                    </Tab.Panel>
                  </Tab.Panels>
                </Tab.Group>
              </div>
            )}

            {error && <Alert alertType="error">{error.message}</Alert>}
          </div>
        </div>
      </div>
    </IndoorProjectPageLayout>
  );
}

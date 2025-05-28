import axios, { AxiosResponse } from 'axios';
import { Params, useLoaderData } from 'react-router-dom';
import {
  ArrowDownTrayIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';
import { Tab, TabGroup, TabList, TabPanel, TabPanels } from '@headlessui/react';
import { useState } from 'react';

import Alert from '../../../Alert';
import {
  IndoorProjectAPIResponse,
  IndoorProjectDataAPIResponse,
} from './IndoorProject';
import IndoorProjectUploadModal from './IndoorProjectUploadModal';
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

  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [activeTreatment, setActiveTreatment] = useState<string | null>(null);

  const {
    indoorProjectData,
    indoorProjectDataSpreadsheet,
    potModuleVisualizationData,
    potGroupModuleVisualizationData,
    traitModuleVisualizationData,
    isLoading,
    isLoadingData,
    error,
    setPotGroupModuleVisualizationData,
    setTraitModuleVisualizationData,
  } = useIndoorProjectData({ indoorProjectId: indoorProject.id });

  console.log('indoorProjectData:', indoorProjectData);

  const formattedDate = (uploadedFile: IndoorProjectDataAPIResponse): string =>
    new Date(uploadedFile.upload_date.toString()).toLocaleDateString();

  const indoorProjectDataId = indoorProjectData.find(
    ({ file_type }) => file_type === '.xlsx'
  )?.id;

  // Get unique treatments from spreadsheet
  const treatments = indoorProjectDataSpreadsheet
    ? [...new Set(indoorProjectDataSpreadsheet.summary.treatment)]
    : [];

  if (!indoorProject)
    return (
      <div>
        <span>No indoor project found</span>
      </div>
    );

  return (
    <IndoorProjectPageLayout>
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-2">
          <h2 className="truncate" title={indoorProject.title}>
            {indoorProject.title}
          </h2>
          <p className="text-gray-600 line-clamp-3">
            {indoorProject.description}
          </p>
        </div>

        <TabGroup>
          <TabList>
            <Tab className="data-[selected]:bg-accent3 data-[selected]:text-white data-[hover]:underline w-28 shrink-0 rounded-lg p-2 font-medium">
              Data
            </Tab>
            <Tab className="data-[selected]:bg-accent3 data-[selected]:text-white data-[hover]:underline w-28 shrink-0 rounded-lg p-2 font-medium">
              Viz
            </Tab>
          </TabList>
          <hr className="my-4 border-gray-700" />
          <TabPanels>
            <TabPanel>
              <div className="flex flex-col gap-8">
                <IndoorProjectUploadForm
                  indoorProjectId={indoorProject.id}
                  indoorProjectData={indoorProjectData}
                  indoorProjectDataSpreadsheet={
                    indoorProjectDataSpreadsheet || undefined
                  }
                />
              </div>
            </TabPanel>
            <TabPanel>
              {isLoading && <LoadingBars />}

              {!isLoading && indoorProjectData.length === 0 && null}

              {!isLoading && indoorProjectData.length > 0 && (
                <div className="w-full flex flex-col gap-4">
                  <span className="text-lg font-bold">
                    Pots
                    {indoorProjectDataSpreadsheet
                      ? ` (${
                          Object.keys(indoorProjectDataSpreadsheet.records)
                            .length
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

                  {indoorProjectDataSpreadsheet &&
                    potModuleVisualizationData && (
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
            </TabPanel>
          </TabPanels>
        </TabGroup>
      </div>

      <IndoorProjectUploadModal
        indoorProjectId={indoorProject.id}
        btnLabel={
          activeTreatment
            ? `Upload ${activeTreatment} TAR`
            : 'Upload Spreadsheet'
        }
        isOpen={isUploadModalOpen}
        setIsOpen={setIsUploadModalOpen}
        hideBtn={true}
      />
    </IndoorProjectPageLayout>
  );
}

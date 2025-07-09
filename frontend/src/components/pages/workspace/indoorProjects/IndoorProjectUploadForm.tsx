import { DocumentIcon } from '@heroicons/react/24/solid';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { useState } from 'react';
import {
  IndoorProjectDataAPIResponse,
  IndoorProjectDataSpreadsheetAPIResponse,
} from './IndoorProject.d';
import IndoorProjectUploadModal from './IndoorProjectUploadModal';

interface IndoorProjectUploadFormProps {
  indoorProjectId: string;
  indoorProjectData: IndoorProjectDataAPIResponse[];
  indoorProjectDataSpreadsheet?: IndoorProjectDataSpreadsheetAPIResponse;
  onUploadSuccess?: () => void;
}

export default function IndoorProjectUploadForm({
  indoorProjectId,
  indoorProjectData,
  indoorProjectDataSpreadsheet,
  onUploadSuccess,
}: IndoorProjectUploadFormProps) {
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [activeTreatment, setActiveTreatment] = useState<string | null>(null);

  // Check if spreadsheet data exists
  const hasSpreadsheet = !!indoorProjectDataSpreadsheet;

  // Get unique treatments from spreadsheet
  const treatments = hasSpreadsheet
    ? [...new Set(indoorProjectDataSpreadsheet.summary.treatment)].filter(
        (treatment): treatment is string => typeof treatment === 'string'
      )
    : [];

  const formattedDate = (uploadedFile: IndoorProjectDataAPIResponse): string =>
    new Date(uploadedFile.upload_date.toString()).toLocaleDateString();

  return (
    <div className="space-y-6">
      {/* Step 1: Upload Experiment */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Step 1: Upload Experiment
        </h3>
        <div className="p-4 bg-white rounded-lg shadow">
          <h4 className="font-medium text-gray-900">Experiment Spreadsheet</h4>
          <p className="text-sm text-gray-500">
            Upload your experiment spreadsheet (.xls or .xlsx) containing plant
            data.
          </p>
          <hr className="my-3 border-gray-300" />
          <div className="flex items-start justify-between">
            <div className="flex-1">
              {indoorProjectData.find((data) => data.file_type === '.xlsx') ? (
                <>
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <DocumentIcon className="w-4 h-4 text-gray-400" />
                    <div className="min-w-0 max-w-md">
                      <a
                        href={
                          indoorProjectData.find(
                            (data) => data.file_type === '.xlsx'
                          )?.file_path
                        }
                        download
                        className="font-medium text-blue-600 hover:text-blue-800 hover:underline truncate block"
                        title={`Download: ${
                          indoorProjectData.find(
                            (data) => data.file_type === '.xlsx'
                          )?.original_filename
                        }`}
                      >
                        {
                          indoorProjectData.find(
                            (data) => data.file_type === '.xlsx'
                          )?.original_filename
                        }
                      </a>
                    </div>
                    <button
                      type="button"
                      title="Remove Spreadsheet"
                      className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                    >
                      <XMarkIcon className="w-4 h-4" />
                    </button>
                  </div>
                  <div className="text-sm text-gray-500 italic mt-2">
                    Uploaded on{' '}
                    {formattedDate(
                      indoorProjectData.find(
                        (data) => data.file_type === '.xlsx'
                      )!
                    )}
                  </div>
                </>
              ) : (
                <div className="text-sm text-gray-500">
                  No spreadsheet uploaded yet
                </div>
              )}
            </div>
            <button
              type="button"
              onClick={() => setIsUploadModalOpen(true)}
              className="ml-4 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              title="Upload Spreadsheet"
            >
              Upload File
            </button>
          </div>
        </div>
      </div>

      {/* Step 2: Treatment Uploads */}
      {hasSpreadsheet && treatments.length > 0 && (
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Step 2: Upload Treatment Data
          </h3>
          <div className="p-4 bg-white rounded-lg shadow space-y-6">
            {treatments.map((treatment) => {
              const uploadedData = indoorProjectData.find(
                (data) =>
                  data.file_type === '.tar' && data.treatment === treatment
              );
              return (
                <div key={treatment}>
                  <h4 className="font-medium text-gray-900">{treatment}</h4>
                  <p className="mt-1 text-sm text-gray-500">
                    Upload TAR archive containing treatment data.
                  </p>
                  <hr className="my-3 border-gray-300" />
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      {uploadedData ? (
                        uploadedData.is_initial_processing_completed ? (
                          <>
                            <div className="flex items-center gap-2 text-sm text-gray-600">
                              <DocumentIcon className="w-4 h-4 text-gray-400" />
                              <div className="min-w-0 max-w-md">
                                <a
                                  href={uploadedData.file_path}
                                  download
                                  className="font-medium text-blue-600 hover:text-blue-800 hover:underline truncate block"
                                  title={`Download: ${uploadedData.original_filename}`}
                                >
                                  {uploadedData.original_filename}
                                </a>
                              </div>
                              <button
                                type="button"
                                title="Remove TAR archive"
                                className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                              >
                                <XMarkIcon className="w-4 h-4" />
                              </button>
                            </div>
                            <div className="text-sm text-gray-500 italic mt-2">
                              Uploaded on {formattedDate(uploadedData)}
                            </div>
                          </>
                        ) : (
                          <div className="flex items-center gap-2 text-amber-600">
                            <div className="w-4 h-4 border-2 border-amber-600 border-t-transparent rounded-full animate-spin"></div>
                            <div>
                              <div className="text-sm font-medium">
                                Processing
                              </div>
                              <div className="text-xs text-gray-500">
                                This may take several minutes
                              </div>
                            </div>
                          </div>
                        )
                      ) : (
                        <div className="text-sm text-gray-500">
                          No file uploaded yet
                        </div>
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        setActiveTreatment(treatment);
                        setIsUploadModalOpen(true);
                      }}
                      className="ml-4 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                      title="Upload TAR archive"
                    >
                      Upload File
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
      <IndoorProjectUploadModal
        activeTreatment={activeTreatment}
        indoorProjectId={indoorProjectId}
        btnLabel={
          activeTreatment
            ? `Upload ${activeTreatment} TAR`
            : 'Upload Spreadsheet'
        }
        isOpen={isUploadModalOpen}
        setIsOpen={setIsUploadModalOpen}
        hideBtn={true}
        fileType={activeTreatment ? '.tar' : '.xlsx'}
        onUploadSuccess={onUploadSuccess}
      />
    </div>
  );
}

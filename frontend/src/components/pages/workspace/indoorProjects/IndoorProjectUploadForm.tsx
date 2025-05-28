import { CheckCircleIcon } from '@heroicons/react/24/solid';
import { ArrowDownTrayIcon } from '@heroicons/react/24/outline';
import { useState } from 'react';
import {
  IndoorProjectDataAPIResponse,
  IndoorProjectDataSpreadsheetAPIResponse,
} from './IndoorProject';
import IndoorProjectUploadModal from './IndoorProjectUploadModal';

interface IndoorProjectUploadFormProps {
  indoorProjectId: string;
  indoorProjectData: IndoorProjectDataAPIResponse[];
  indoorProjectDataSpreadsheet?: IndoorProjectDataSpreadsheetAPIResponse;
}

export default function IndoorProjectUploadForm({
  indoorProjectId,
  indoorProjectData,
  indoorProjectDataSpreadsheet,
}: IndoorProjectUploadFormProps) {
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [activeTreatment, setActiveTreatment] = useState<string | null>(null);

  // Check if spreadsheet data exists
  const hasSpreadsheet = !!indoorProjectDataSpreadsheet;

  // Get unique treatments from spreadsheet
  const treatments = hasSpreadsheet
    ? [...new Set(indoorProjectDataSpreadsheet.summary.treatment)]
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
        <div className="flex items-center gap-4 p-4 bg-white rounded-lg shadow">
          <div className="flex-1">
            <h4 className="font-medium text-gray-900">
              Experiment Spreadsheet
            </h4>
            <p className="text-sm text-gray-500">
              Upload your experiment spreadsheet (.xls or .xlsx) containing
              plant data.
            </p>
            {indoorProjectData.find((data) => data.file_type === '.xlsx') && (
              <div className="mt-2 text-sm text-gray-600">
                <div className="font-medium">
                  {
                    indoorProjectData.find((data) => data.file_type === '.xlsx')
                      ?.original_filename
                  }
                </div>
                <div className="flex items-end gap-2">
                  <span className="italic">
                    Uploaded on{' '}
                    {formattedDate(
                      indoorProjectData.find(
                        (data) => data.file_type === '.xlsx'
                      )!
                    )}
                  </span>
                  <a
                    href={
                      indoorProjectData.find(
                        (data) => data.file_type === '.xlsx'
                      )?.file_path
                    }
                    download
                    className="inline-flex items-center text-blue-600 hover:text-blue-800"
                  >
                    <ArrowDownTrayIcon className="w-4 h-4 mr-1" />
                    Download
                  </a>
                </div>
              </div>
            )}
          </div>
          {hasSpreadsheet ? (
            <div className="flex items-center gap-2 text-green-600">
              <CheckCircleIcon className="w-6 h-6" />
              <span className="text-sm font-medium">Spreadsheet uploaded</span>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => setIsUploadModalOpen(true)}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Upload Spreadsheet
            </button>
          )}
        </div>
      </div>

      {/* Step 2: Treatment Uploads */}
      {hasSpreadsheet && treatments.length > 0 && (
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Step 2: Upload Treatment Data
          </h3>
          <div className="grid gap-4">
            {treatments.map((treatment) => {
              const uploadedData = indoorProjectData.find(
                (data) =>
                  data.file_type === '.tar' &&
                  data.directory_structure?.name === treatment
              );
              return (
                <div
                  key={treatment}
                  className="flex items-center gap-4 p-4 bg-white rounded-lg shadow"
                >
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900">{treatment}</h4>
                    <p className="mt-1 text-sm text-gray-500">
                      Upload TAR archive containing treatment data
                    </p>
                    {uploadedData && (
                      <div className="mt-2 text-sm text-gray-600">
                        <div className="font-medium">
                          {uploadedData.original_filename}
                        </div>
                        <div className="flex items-end gap-2">
                          <span className="italic">
                            Uploaded on {formattedDate(uploadedData)}
                          </span>
                          <a
                            href={uploadedData.file_path}
                            download
                            className="inline-flex items-center text-blue-600 hover:text-blue-800"
                          >
                            <ArrowDownTrayIcon className="w-4 h-4 mr-1" />
                            Download
                          </a>
                        </div>
                      </div>
                    )}
                  </div>
                  {uploadedData ? (
                    <div className="flex items-center gap-2 text-green-600">
                      <CheckCircleIcon className="w-6 h-6" />
                      <span className="text-sm font-medium">TAR Uploaded</span>
                    </div>
                  ) : (
                    <button
                      type="button"
                      onClick={() => {
                        setActiveTreatment(treatment);
                        setIsUploadModalOpen(true);
                      }}
                      className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      Upload TAR
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      <IndoorProjectUploadModal
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
      />
    </div>
  );
}

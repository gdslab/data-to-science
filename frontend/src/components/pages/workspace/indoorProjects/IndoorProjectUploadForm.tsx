import { DocumentIcon } from '@heroicons/react/24/solid';

import {
  IndoorProjectDataAPIResponse,
  IndoorProjectDataSpreadsheetAPIResponse,
} from './IndoorProject.d';
import IndoorProjectUploadInline from './IndoorProjectUploadInline';

interface IndoorProjectUploadFormProps {
  indoorProjectId: string;
  indoorProjectData: IndoorProjectDataAPIResponse[];
  indoorProjectDataSpreadsheet?: IndoorProjectDataSpreadsheetAPIResponse;
  onUploadSuccess?: () => void;
  onUploadStateChange?: (isUploading: boolean) => void;
}

export default function IndoorProjectUploadForm({
  indoorProjectId,
  indoorProjectData,
  indoorProjectDataSpreadsheet,
  onUploadSuccess,
  onUploadStateChange,
}: IndoorProjectUploadFormProps) {

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
          {indoorProjectData.find((data) => data.file_type === '.xlsx') ? (
            <div className="flex items-center gap-2 text-sm text-gray-600 min-w-0">
              <DocumentIcon className="w-4 h-4 text-gray-400" />
              <div className="flex-1 min-w-0 overflow-hidden">
                <a
                  href={
                    indoorProjectData.find(
                      (data) => data.file_type === '.xlsx'
                    )?.file_path
                  }
                  download
                  className="font-medium text-blue-600 hover:text-blue-800 hover:underline truncate block"
                  title={
                    indoorProjectData.find(
                      (data) => data.file_type === '.xlsx'
                    )?.original_filename
                  }
                >
                  {
                    indoorProjectData.find(
                      (data) => data.file_type === '.xlsx'
                    )?.original_filename
                  }
                </a>
              </div>
            </div>
          ) : (
            <IndoorProjectUploadInline
              indoorProjectId={indoorProjectId}
              fileType=".xlsx"
              onUploadSuccess={onUploadSuccess}
              onUploadStateChange={onUploadStateChange}
            />
          )}
          {indoorProjectData.find((data) => data.file_type === '.xlsx') && (
            <div className="text-sm text-gray-500 italic mt-2">
              Uploaded on{' '}
              {formattedDate(
                indoorProjectData.find(
                  (data) => data.file_type === '.xlsx'
                )!
              )}
            </div>
          )}
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
                  {uploadedData ? (
                    uploadedData.is_initial_processing_completed ? (
                      <>
                        <div className="flex items-center gap-2 text-sm text-gray-600 min-w-0">
                          <DocumentIcon className="w-4 h-4 text-gray-400" />
                          <div className="flex-1 min-w-0 overflow-hidden">
                            <a
                              href={uploadedData.file_path}
                              download
                              className="font-medium text-blue-600 hover:text-blue-800 hover:underline truncate block"
                              title={uploadedData.original_filename}
                            >
                              {uploadedData.original_filename}
                            </a>
                          </div>
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
                    <IndoorProjectUploadInline
                      indoorProjectId={indoorProjectId}
                      fileType=".tar"
                      activeTreatment={treatment}
                      onUploadSuccess={onUploadSuccess}
                      onUploadStateChange={onUploadStateChange}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

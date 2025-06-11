import { XCircleIcon } from '@heroicons/react/24/solid';
import { BreedBaseStudy } from './BreedBase.types';

interface BreedBaseStudiesTableProps {
  studies: BreedBaseStudy[];
  studyDetails: Record<string, { studyName: string; seasons: string }>;
  loadingStudyDetails: Record<string, boolean>;
  onRemoveStudy: (studyId: string) => void;
}

export default function BreedBaseStudiesTable({
  studies,
  studyDetails,
  loadingStudyDetails,
  onRemoveStudy,
}: BreedBaseStudiesTableProps) {
  if (studies.length === 0) {
    return <div>No studies found</div>;
  }

  return (
    <div className="overflow-x-auto max-h-96 overflow-y-auto">
      <table className="min-w-full bg-white border border-gray-200 rounded-lg">
        <thead>
          <tr className="bg-gray-50 border-b border-gray-200">
            <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
              Base URL
            </th>
            <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
              Study ID
            </th>
            <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
              Study Name
            </th>
            <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
              Seasons
            </th>
            <th className="text-center py-3 px-4 text-sm font-medium text-gray-500 w-20">
              Remove
            </th>
          </tr>
        </thead>
        <tbody>
          {studies.map((study) => {
            const studyKey = `${study.base_url}-${study.study_id}`;
            const details = studyDetails[studyKey];
            const isLoadingDetails = loadingStudyDetails[studyKey];

            return (
              <tr
                key={study.id}
                className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
              >
                <td
                  className="py-3 px-4 text-gray-700 truncate max-w-xs"
                  title={study.base_url}
                >
                  {study.base_url}
                </td>
                <td className="py-3 px-4 text-gray-700" title={study.study_id}>
                  {study.study_id}
                </td>
                <td
                  className="py-3 px-4 text-gray-700"
                  title={details?.studyName || 'Loading...'}
                >
                  {isLoadingDetails ? (
                    <span className="text-gray-400 italic">Loading...</span>
                  ) : (
                    details?.studyName || 'Unknown'
                  )}
                </td>
                <td
                  className="py-3 px-4 text-gray-700"
                  title={details?.seasons || 'Loading...'}
                >
                  {isLoadingDetails ? (
                    <span className="text-gray-400 italic">Loading...</span>
                  ) : (
                    details?.seasons || 'N/A'
                  )}
                </td>
                <td className="py-3 px-4 text-center">
                  <button
                    className="text-red-500 hover:text-red-700 transition-colors inline-flex items-center justify-center"
                    onClick={() => onRemoveStudy(study.id)}
                    title="Remove connection"
                  >
                    <XCircleIcon className="h-5 w-5" />
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

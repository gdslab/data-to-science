import { BreedBaseStudiesAPIResponse } from './BreedBase.types';

import Pagination from '../../../../Pagination';

export default function BreedBaseStudies({
  data,
  onAddStudyId,
  onPageChange,
}: {
  data: BreedBaseStudiesAPIResponse;
  onAddStudyId: (studyId: string) => void;
  onPageChange: (page: number) => void;
}) {
  return (
    <div className="h-full mb-4">
      <h3>Studies</h3>
      <div className="flex flex-col gap-4 h-48 xl:h-64 2xl:h-72">
        <div className="flex-1 overflow-y-auto">
          <table className="min-w-full divide-y-2 divide-gray-200 bg-white text-sm">
            <thead className="text-left sticky top-0 z-10 bg-white">
              <tr>
                <th className="whitespace-nowrap px-4 py-2 font-medium text-gray-900">
                  Study ID
                </th>
                <th className="whitespace-nowrap px-4 py-2 font-medium text-gray-900">
                  Study Name
                </th>
                <th className="whitespace-nowrap px-4 py-2 font-medium text-gray-900">
                  Study Description
                </th>
                <th className="whitespace-nowrap px-4 py-2 font-medium text-gray-900">
                  Program
                </th>
                <th className="whitespace-nowrap px-4 py-2 font-medium text-gray-900">
                  Seasons
                </th>
                <th className="whitespace-nowrap px-4 py-2 font-medium text-gray-900">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {data.result.data.map((study) => (
                <tr key={study.studyDbId} className="odd:bg-gray-50">
                  <td className="px-4 py-2">{study.studyDbId}</td>
                  <td className="px-4 py-2">{study.studyName}</td>
                  <td className="px-4 py-2">{study.studyDescription}</td>
                  <td className="px-4 py-2">
                    {study.additionalInfo?.programName}
                  </td>
                  <td className="px-4 py-2">{study.seasons.join(', ')}</td>
                  <td className="px-4 py-2">
                    <button
                      onClick={() => onAddStudyId(study.studyDbId)}
                      className="bg-accent2/90 text-white font-semibold px-2 py-1 rounded enabled:hover:bg-accent2 disabled:opacity-75 disabled:cursor-not-allowed"
                    >
                      Add
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <Pagination
          currentPage={data.metadata.pagination.currentPage}
          totalPages={data.metadata.pagination.totalPages}
          updateCurrentPage={onPageChange}
        />
      </div>
    </div>
  );
}

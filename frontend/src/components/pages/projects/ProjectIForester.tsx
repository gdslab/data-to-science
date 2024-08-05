import axios, { AxiosResponse, isAxiosError } from 'axios';
import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';

import { IForester } from './Project';
import IForesterList from './iForester/IForesterList';
import TableCardRadioInput from '../../TableCardRadioInput';
import IForesterTable from './iForester/IForesterTable';

import { sorter } from '../../utils';

function getIForesterDisplayModeFromLS(): 'table' | 'carousel' {
  const iforesterDisplayMode = localStorage.getItem('iforesterDisplayMode');
  if (iforesterDisplayMode === 'table' || iforesterDisplayMode === 'carousel') {
    return iforesterDisplayMode;
  } else {
    localStorage.setItem('iforesterDisplayMode', 'carousel');
    return 'carousel';
  }
}

export default function ProjectIForester() {
  const [iforesterData, setIForesterData] = useState<IForester[]>([]);
  const [iForesterSortOrder, setIForesterSortOrder] = useState('asc');
  const [tableView, toggleTableView] = useState<'table' | 'carousel'>(
    getIForesterDisplayModeFromLS()
  );

  const params = useParams();

  useEffect(() => {
    async function fetchIForesterData(projectId: string) {
      try {
        const response: AxiosResponse<IForester[]> = await axios.get(
          `${import.meta.env.VITE_API_V1_STR}/projects/${projectId}/iforester`
        );
        if (response.status === 200) {
          setIForesterData(response.data);
        } else {
          return [];
        }
      } catch (err) {
        if (isAxiosError(err) && err.response) {
          console.error(err.response.data);
        } else {
          console.error(err);
        }
        return [];
      }
    }
    if (params.projectId) {
      fetchIForesterData(params.projectId);
    }
  }, []);

  function onTableViewChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.value === 'carousel' || e.target.value === 'table') {
      localStorage.setItem('iforesterDisplayMode', e.target.value);
      toggleTableView(e.target.value);
    }
  }

  return (
    <div className="grow min-h-0">
      <div className="h-full flex flex-col gap-4">
        <div className="h-24">
          <h2>iForester</h2>
          <div className="flex justify-between">
            <div className="flex flex-row gap-8">
              <div className="flex flex-row items-center gap-2">
                <label
                  htmlFor="iForesterSortOrder"
                  className="text-sm font-medium text-gray-900 w-20"
                >
                  Sort by
                </label>
                <select
                  name="iForesterSortOrder"
                  id="iForesterSortOrder"
                  className="w-full px-1.5 font-semibold rounded-md border-2 border-zinc-300 text-gray-700 sm:text-sm"
                  onChange={(e) => setIForesterSortOrder(e.target.value)}
                >
                  <option value="asc">Date (ascending)</option>
                  <option value="desc">Date (descending)</option>
                </select>
              </div>
            </div>
            <TableCardRadioInput
              tableView={tableView}
              toggleTableView={onTableViewChange}
            />
          </div>
        </div>
        {tableView === 'table' ? (
          <IForesterTable
            data={useMemo(
              () =>
                iforesterData.sort((a, b) =>
                  sorter(
                    new Date(a.timeStamp),
                    new Date(b.timeStamp),
                    iForesterSortOrder
                  )
                ),
              [iforesterData, iForesterSortOrder]
            )}
          />
        ) : (
          <IForesterList
            data={useMemo(
              () =>
                iforesterData.sort((a, b) =>
                  sorter(
                    new Date(a.timeStamp),
                    new Date(b.timeStamp),
                    iForesterSortOrder
                  )
                ),
              [iforesterData, iForesterSortOrder]
            )}
          />
        )}
        {iforesterData.length === 0 && <span>No submissions</span>}
      </div>
    </div>
  );
}

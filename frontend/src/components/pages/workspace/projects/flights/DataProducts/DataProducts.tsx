import { useMemo, useState } from 'react';
import { useParams, useRevalidator } from 'react-router';

import { DataProduct } from '../../Project';
import { RawDataProps } from '../RawData/RawData.types';
import { Button } from '../../../../../Buttons';
import TableCardRadioInput from '../../../../../TableCardRadioInput';
import DataProductUploadModal from './DataProductUploadModal';
import { useInterval } from '../../../../../hooks';
import DataProductCard from './DataProductCard';
import DataProductsTable from './DataProductsTable';
import { useProjectContext } from '../../ProjectContext';

import { sorter } from '../../../../../utils';
import { AlertBar, Status } from '../../../../../Alert';

function getDataProductsDisplayModeFromLS(): 'table' | 'carousel' {
  const dataProductsDisplayMode = localStorage.getItem(
    'dataProductsDisplayMode'
  );
  if (
    dataProductsDisplayMode === 'table' ||
    dataProductsDisplayMode === 'carousel'
  ) {
    return dataProductsDisplayMode;
  } else {
    localStorage.setItem('dataProductsDisplayMode', 'carousel');
    return 'carousel';
  }
}

export default function DataProducts({
  data,
  rawData,
}: {
  data: DataProduct[];
  rawData: RawDataProps[];
}) {
  const [open, setOpen] = useState(false);
  const [status, setStatus] = useState<Status | null>(null);
  const [tableView, toggleTableView] = useState<'table' | 'carousel'>(
    getDataProductsDisplayModeFromLS()
  );

  const { flightId, projectId } = useParams();
  const revalidator = useRevalidator();

  const { projectRole } = useProjectContext();

  useInterval(
    () => {
      revalidator.revalidate();
    },
    data &&
      data.length > 0 &&
      data.filter(
        ({ status }) => status === 'INPROGRESS' || status === 'WAITING'
      ).length > 0
      ? 5000 // check every 5 seconds while processing job is active
      : 30000 // check every 30 seconds when no known jobs are active
  );

  function handleModalClose() {
    setOpen(false);
    revalidator.revalidate(); // Revalidate when modal closes
  }

  function onTableViewChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.value === 'carousel' || e.target.value === 'table') {
      localStorage.setItem('dataProductsDisplayMode', e.target.value);
      toggleTableView(e.target.value);
    }
  }

  const sortedDataProducts = useMemo(
    () => data.sort((a, b) => sorter(a.data_type, b.data_type)),
    [data]
  );

  // Resolve a product's source raw_data_id to the upload's original filename so
  // the card and table can show which raw data it was generated from.
  const rawDataFilenames = useMemo(
    () => new Map(rawData.map((rd) => [rd.id, rd.original_filename])),
    [rawData]
  );

  return (
    <div className="h-full flex flex-col">
      <div className="h-24">
        <h2>Data Products</h2>
        <TableCardRadioInput
          tableView={tableView}
          toggleTableView={onTableViewChange}
        />
      </div>

      {tableView === 'table' && (
        <DataProductsTable
          data={sortedDataProducts}
          rawDataFilenames={rawDataFilenames}
          setStatus={setStatus}
        />
      )}

      {tableView === 'carousel' && (
        <div className="h-full grow flex flex-cols flex-wrap justify-start gap-4 min-h-[424px] max-h-[424px] lg:max-h-[448px] xl:max-h-[512px] 2xl:max-h-[576px] overflow-y-auto">
          {sortedDataProducts.map((dataProduct) => (
            <DataProductCard
              key={dataProduct.id}
              dataProduct={dataProduct}
              otherDataProducts={sortedDataProducts.filter(
                (dp) => dp.id !== dataProduct.id
              )}
              rawDataFilenames={rawDataFilenames}
              setStatus={setStatus}
            />
          ))}
        </div>
      )}

      {projectRole !== 'viewer' && projectId && flightId ? (
        <div className="my-4 flex justify-center">
          <DataProductUploadModal
            flightID={flightId}
            open={open}
            projectID={projectId}
            handleModalClose={handleModalClose}
          />
          <Button size="sm" onClick={() => setOpen(true)}>
            Upload Data Product
          </Button>
        </div>
      ) : null}
      {status && <AlertBar alertType={status.type}>{status.msg}</AlertBar>}
    </div>
  );
}

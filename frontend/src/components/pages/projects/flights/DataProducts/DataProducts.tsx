import { useEffect, useState } from 'react';
import { useParams, useRevalidator } from 'react-router-dom';

import { Button } from '../../../../Buttons';
import TableCardRadioInput from '../../../../TableCardRadioInput';
import DataProductUploadModal from './DataProductUploadModal';
import { useInterval } from '../../../../hooks';
import DataProductCard from './DataProductCard';
import DataProductsTable from './DataProductsTable';
import { useProjectContext } from '../../ProjectContext';

import { DataProduct } from '../../Project';

function getDataProductsDisplayModeFromLS(): 'table' | 'carousel' {
  const dataProductsDisplayMode = localStorage.getItem('dataProductsDisplayMode');
  if (dataProductsDisplayMode === 'table' || dataProductsDisplayMode === 'carousel') {
    return dataProductsDisplayMode;
  } else {
    localStorage.setItem('dataProductsDisplayMode', 'carousel');
    return 'carousel';
  }
}

export default function DataProducts({ data }: { data: DataProduct[] }) {
  const [open, setOpen] = useState(false);
  const [tableView, toggleTableView] = useState<'table' | 'carousel'>(
    getDataProductsDisplayModeFromLS()
  );

  const { flightId, projectId } = useParams();
  const revalidator = useRevalidator();

  const { projectRole } = useProjectContext();

  useEffect(() => {
    if (!open) revalidator.revalidate();
  }, [open]);

  useInterval(
    () => {
      revalidator.revalidate();
    },
    data &&
      data.length > 0 &&
      data.filter(
        ({ initial_processing_status }) =>
          initial_processing_status === 'INPROGRESS' ||
          initial_processing_status === 'WAITING'
      ).length > 0
      ? 5000 // check every 5 seconds while processing job is active
      : 30000 // check every 30 seconds when no known jobs are active
  );

  function onTableViewChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.value === 'carousel' || e.target.value === 'table') {
      localStorage.setItem('dataProductsDisplayMode', e.target.value);
      toggleTableView(e.target.value);
    }
  }

  return (
    <div className="h-full flex flex-col">
      <div className="h-24">
        <h2>Data Products</h2>
        <TableCardRadioInput
          tableView={tableView}
          toggleTableView={onTableViewChange}
        />
      </div>
      {data.length > 0 ? (
        tableView === 'table' ? (
          <DataProductsTable data={data} />
        ) : (
          <div className="grow flex flex-cols flex-wrap justify-start gap-4 min-h-96 overflow-auto">
            {data.map((dataProduct) => (
              <DataProductCard key={dataProduct.id} dataProduct={dataProduct} />
            ))}
          </div>
        )
      ) : null}
      {projectRole !== 'viewer' && projectId && flightId ? (
        <div className="my-4 flex justify-center">
          <DataProductUploadModal
            flightID={flightId}
            open={open}
            projectID={projectId}
            setOpen={setOpen}
          />
          <Button size="sm" onClick={() => setOpen(true)}>
            Upload Data Product
          </Button>
        </div>
      ) : null}
    </div>
  );
}

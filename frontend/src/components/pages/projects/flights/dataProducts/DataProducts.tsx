import { useEffect, useState } from 'react';
import { useParams, useRevalidator } from 'react-router-dom';

import { Button } from '../../../../Buttons';
import TableCardRadioInput from '../../../../TableCardRadioInput';
import UploadModal from '../../../../UploadModal';
import { useInterval } from '../../../../hooks';
import { DataProductStatus } from '../FlightData';
import DataProductCard from './DataProductCard';
import DataProductsTable from './DataProductsTable';
import { useProjectContext } from '../../ProjectContext';

export default function DataProducts({ data }: { data: DataProductStatus[] }) {
  const { flightId, projectId } = useParams();
  const [open, setOpen] = useState(false);
  const [tableView, toggleTableView] = useState<'table' | 'carousel'>('carousel');
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
      data.filter(({ status }) => status === 'INPROGRESS').length > 0
      ? 30000 // 30 seconds
      : null
  );

  return (
    <div className="h-full flex flex-col">
      <div className="h-24">
        <h2>Data Products</h2>
        <TableCardRadioInput tableView={tableView} toggleTableView={toggleTableView} />
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
      {projectRole !== 'viewer' ? (
        <div className="my-4 flex justify-center">
          <UploadModal
            apiRoute={`/api/v1/projects/${projectId}/flights/${flightId}`}
            open={open}
            setOpen={setOpen}
          />
          <Button size="sm" onClick={() => setOpen(true)}>
            Upload Data
          </Button>
        </div>
      ) : null}
    </div>
  );
}

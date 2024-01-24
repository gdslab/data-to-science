import { useEffect, useState } from 'react';
import { useParams, useRevalidator } from 'react-router-dom';

import { Button } from '../../../../Buttons';
import { RawData as RawDataInterface } from '../FlightData';
import Table, { TableBody, TableHead } from '../../../../Table';
import UploadModal from '../../../../UploadModal';

export default function RawData({
  data,
  role,
}: {
  data: RawDataInterface[];
  role: string;
}) {
  const { projectId, flightId } = useParams();
  const [open, setOpen] = useState(false);
  const revalidator = useRevalidator();

  useEffect(() => {
    if (!open) revalidator.revalidate();
  }, [open]);

  return (
    <>
      <h2>Raw Data</h2>
      {data.length > 0 ? (
        <div className="mt-4">
          <Table height={48}>
            <TableHead columns={['Filename', 'Download']} />
            <TableBody
              rows={data.map((dataset) => [
                dataset.original_filename,
                <a
                  className="flex justify-center"
                  href={dataset.url}
                  download="rawdata.zip"
                  target="_blank"
                >
                  <Button size="sm">Download (.zip)</Button>
                </a>,
              ])}
            />
          </Table>
        </div>
      ) : (
        <span>No raw data has been uploaded</span>
      )}
      {role !== 'viewer' ? (
        <div>
          <UploadModal
            apiRoute={`/api/v1/projects/${projectId}/flights/${flightId}/raw_data`}
            open={open}
            setOpen={setOpen}
            uploadType="zip"
          />
          <div className="w-48">
            <Button size="sm" onClick={() => setOpen(true)}>
              Upload Raw Data (.zip)
            </Button>
          </div>
        </div>
      ) : null}
    </>
  );
}

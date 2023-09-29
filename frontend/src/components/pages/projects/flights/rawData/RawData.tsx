import { useState } from 'react';
import { useParams } from 'react-router-dom';

import { Button } from '../../../../Buttons';
import { RawData as RawDataInterface } from '../FlightData';
import Table, { TableBody, TableHead } from '../../../../Table';
import UploadModal from '../../../../UploadModal';

export default function RawData({ data }: { data: RawDataInterface[] }) {
  const { projectId, flightId } = useParams();
  const [open, setOpen] = useState(false);
  return (
    <div>
      <h2>Raw Data</h2>
      {data.length > 0 ? (
        <div className="mt-4">
          <Table>
            <TableHead columns={['Filename', 'Download']} />
            <TableBody
              rows={data.map((dataset) => [
                dataset.original_filename,
                <a href={dataset.url} download="rawdata.zip" target="_blank">
                  <Button size="sm">Download (.zip)</Button>
                </a>,
              ])}
            />
          </Table>
        </div>
      ) : null}
      <div className="my-4">
        <UploadModal
          apiRoute={`/api/v1/projects/${projectId}/flights/${flightId}/raw_data`}
          open={open}
          setOpen={setOpen}
          uploadType="zip"
        />
        <Button size="sm" onClick={() => setOpen(true)}>
          Upload Raw Data (.zip)
        </Button>
      </div>
    </div>
  );
}

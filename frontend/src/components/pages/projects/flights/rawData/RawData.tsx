import axios from 'axios';
import { useState } from 'react';
import { Params, useLoaderData, useParams } from 'react-router-dom';

import { Button } from '../../../../Buttons';
import Table, { TableBody, TableHead } from '../../../../Table';
import UploadModal from '../../../../UploadModal';

export async function loader({ params }: { params: Params<string> }) {
  try {
    const rawData = await axios.get(
      `/api/v1/projects/${params.projectId}/flights/${params.flightId}/raw_data`
    );
    if (rawData) {
      return rawData.data;
    } else {
      return [];
    }
  } catch (err) {
    console.error('Unable to retrieve raw data');
    return [];
  }
}

interface Data {
  original_filename: string;
  url: string;
}

export default function RawData() {
  const data = useLoaderData() as Data[];
  const { projectId, flightId } = useParams();
  const [open, setOpen] = useState(false);
  return (
    <div className="mt-4">
      <h2>Raw Data</h2>
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

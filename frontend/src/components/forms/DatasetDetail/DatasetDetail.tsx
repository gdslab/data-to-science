import axios from 'axios';
import { Params, useParams } from 'react-router-dom';
import { useState } from 'react';

import { Button } from '../Buttons';
import FileUpload from '../../FileUpload';
import UploadModal from '../../UploadModal';

export async function loader({ params }: { params: Params<string> }) {
  const response = await axios.get(
    `/api/v1/projects/${params.projectId}/datasets/${params.datasetId}`
  );
  if (response) {
    return response.data;
  } else {
    return null;
  }
}

export default function DatasetDetail() {
  const [open, setOpen] = useState(false);
  const { datasetId, projectId } = useParams();
  return (
    <div className="">
      <div className="m-4">
        <div className="w-48">
          <FileUpload
            restrictions={{ allowedFileTypes: ['.tif'], maxNumberOfFiles: 1 }}
            upload_endpoint={`/api/v1/projects/${projectId}/datasets/${datasetId}/raw_data`}
          />
        </div>
      </div>
    </div>
  );
}

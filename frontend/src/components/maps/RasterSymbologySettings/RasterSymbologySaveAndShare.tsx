import { AxiosResponse } from 'axios';
import { useState } from 'react';

import { Button } from '../../Buttons';
import {
  DataProduct,
  ProjectDetail,
  ProjectItem,
} from '../../pages/workspace/projects/Project';
import Modal from '../../Modal';
import RasterSymbologyAccessControls from './RasterSymbologyAccessControls';
import { useMapContext } from '../MapContext';
import {
  MultibandSymbology,
  SingleBandSymbology,
  useRasterSymbologyContext,
} from '../RasterSymbologyContext';

import api from '../../../api';

function RasterSymbologyShare({
  dataProduct,
  project,
  symbology,
}: {
  dataProduct: DataProduct;
  project: ProjectDetail | ProjectItem;
  symbology: SingleBandSymbology | MultibandSymbology;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div className="w-36">
      <Button
        type="button"
        size="sm"
        icon="share2"
        onClick={() => setOpen(true)}
      >
        Share
      </Button>
      <Modal open={open} setOpen={setOpen}>
        <RasterSymbologyAccessControls
          dataProduct={dataProduct}
          project={project}
          symbology={symbology}
        />
      </Modal>
    </div>
  );
}

type RasterSymbologySaveProps = {
  dataProduct: DataProduct;
  projectId: string;
  symbology: SingleBandSymbology | MultibandSymbology;
};

type StyleResponse = {
  id: string;
  settings: SingleBandSymbology | MultibandSymbology;
  data_product_id: string;
  user_id: string;
};

function RasterSymbologySave({
  dataProduct,
  projectId,
  symbology,
}: RasterSymbologySaveProps) {
  const { dispatch } = useRasterSymbologyContext();
  const [isSaving, setIsSaving] = useState(false);

  const saveSymbology = async (dataProduct, projectId, symbology) => {
    setIsSaving(true);
    const startTime = Date.now();

    try {
      const axiosRequest = dataProduct.user_style ? api.put : api.post;
      const response: AxiosResponse<StyleResponse> = await axiosRequest(
        `/projects/${projectId}/flights/${dataProduct.flight_id}/data_products/${dataProduct.id}/style`,
        { settings: symbology }
      );
      if (response) {
        dispatch({
          type: 'SET_SYMBOLOGY',
          rasterId: dataProduct.id,
          payload: response.data.settings,
        });
      } else {
        console.error('Unable to update symbology');
      }
    } catch (err) {
      console.error(err);
    } finally {
      // Ensure loading state shows for at least 3 seconds
      const elapsedTime = Date.now() - startTime;
      const remainingTime = Math.max(0, 3000 - elapsedTime);
      setTimeout(() => setIsSaving(false), remainingTime);
    }
  };

  return (
    <div className="w-36">
      <Button
        type="button"
        size="sm"
        onClick={() => saveSymbology(dataProduct, projectId, symbology)}
        disabled={isSaving}
      >
        {isSaving ? 'Saving...' : 'Save Changes'}
      </Button>
    </div>
  );
}

export default function RasterSymbologySaveAndShare({
  dataProduct,
}: {
  dataProduct: DataProduct;
}) {
  const { activeProject } = useMapContext();

  const { state } = useRasterSymbologyContext();

  const symbology = state[dataProduct.id].symbology;

  if (!activeProject || !symbology) return null;

  return (
    <div className="mt-4 w-full flex items-center justify-between">
      <RasterSymbologyShare
        dataProduct={dataProduct}
        project={activeProject}
        symbology={symbology}
      />
      <RasterSymbologySave
        dataProduct={dataProduct}
        projectId={activeProject.id}
        symbology={symbology}
      />
    </div>
  );
}

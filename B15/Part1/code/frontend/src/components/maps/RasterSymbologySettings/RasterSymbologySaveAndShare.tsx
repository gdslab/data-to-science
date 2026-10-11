import { AxiosResponse } from 'axios';
import { useEffect, useState } from 'react';

import Alert, { Status } from '../../Alert';
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
import { exportDataProductToJpeg, isPublicOnly } from '../utils';

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
    <div className="flex-1 min-w-32 max-md:w-full">
      <Button
        type="button"
        size="sm"
        icon="share2"
        onClick={() => setOpen(true)}
      >
        Share
      </Button>
      <Modal open={open} setOpen={setOpen} overflow="visible">
        <RasterSymbologyAccessControls
          dataProduct={dataProduct}
          project={project}
          symbology={symbology}
        />
      </Modal>
    </div>
  );
}

type RasterSymbologyExportProps = {
  dataProduct: DataProduct;
  projectId: string;
  symbology: SingleBandSymbology | MultibandSymbology;
  setStatus: React.Dispatch<React.SetStateAction<Status | null>>;
};

function RasterSymbologyExport({
  dataProduct,
  projectId,
  symbology,
  setStatus,
}: RasterSymbologyExportProps) {
  const [isExporting, setIsExporting] = useState(false);

  const exportImage = async () => {
    setIsExporting(true);
    setStatus(null);

    try {
      // Uses the symbology in context, not the saved style, so unsaved changes
      // are included in the exported image
      await exportDataProductToJpeg(dataProduct, projectId, symbology);
    } catch (err) {
      console.error(err);
      setStatus({
        type: 'error',
        msg: 'Unable to export image. Please try again.',
      });
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="flex-1 min-w-32 max-md:w-full">
      <Button
        type="button"
        size="sm"
        onClick={exportImage}
        disabled={isExporting}
        // The export matches the map's colors but not its transparency, which a
        // JPG cannot carry, so say so before the download rather than after
        title="Export a JPG using the current map settings. Areas with no data appear black."
      >
        {isExporting ? 'Exporting...' : 'Export JPG'}
      </Button>
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
    <div className="flex-1 min-w-32 max-md:w-full">
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
  const [stacBrowserUrl, setStacBrowserUrl] = useState<string>('');
  const [status, setStatus] = useState<Status | null>(null);

  useEffect(() => {
    fetch('/config.json')
      .then((r) => r.json())
      .then((cfg) => setStacBrowserUrl(cfg.stacBrowserUrl || ''))
      .catch(() => setStacBrowserUrl(''));
  }, []);

  const symbology = state[dataProduct.id].symbology;

  if (!activeProject || !symbology) return null;

  return (
    <div className="mt-4 w-full flex flex-col gap-2">
      <div className="w-full flex flex-wrap items-center justify-between gap-2 max-md:flex-col max-md:items-stretch">
        {isPublicOnly(activeProject)
          ? stacBrowserUrl && (
              <div className="w-full">
                <a
                  href={`${stacBrowserUrl}/collections/${activeProject.id}/items/${dataProduct.id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  title="Open in STAC Browser (opens in a new tab)"
                  className="inline-flex items-center justify-center w-full text-sm font-bold py-1.5 px-4 border-2 rounded-md bg-accent3 hover:bg-accent3-dark border-accent3 hover:border-accent3-dark text-white ease-in-out duration-300"
                >
                  Open in STAC Browser
                </a>
              </div>
            )
          : (
            <RasterSymbologyShare
              dataProduct={dataProduct}
              project={activeProject}
              symbology={symbology}
            />
          )}
        {activeProject.role && (
          <RasterSymbologyExport
            dataProduct={dataProduct}
            projectId={activeProject.id}
            symbology={symbology}
            setStatus={setStatus}
          />
        )}
        {activeProject.role && (
          <RasterSymbologySave
            dataProduct={dataProduct}
            projectId={activeProject.id}
            symbology={symbology}
          />
        )}
      </div>
      {status && <Alert alertType={status.type}>{status.msg}</Alert>}
    </div>
  );
}

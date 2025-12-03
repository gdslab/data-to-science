import { AxiosResponse, isAxiosError } from 'axios';
import { useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  PhotoIcon,
  PencilIcon,
  CheckIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';

import { MapLayer, MapLayerFeatureCollection } from '../Project';
import MapLayerDownloadLinks from './MapLayerDownloadLink';
import ConfirmationModal from '../../../ConfirmationModal';
import ImagePreviewModal from './ImagePreviewModal';
import { getMapLayers, useProjectContext } from '../ProjectContext';
import { AlertBar, Status } from '../../../Alert';
import { useInterval } from '../../../hooks';

import api from '../../../../api';

import pointIcon from '../../../../assets/point-icon.svg';
import lineIcon from '../../../../assets/line-icon.svg';
import polygonIcon from '../../../../assets/polygon-icon.svg';

// Polling interval for checking for new map layers (in milliseconds)
const MAP_LAYERS_POLLING_INTERVAL = 30000; // 30 seconds

/**
 * If a "Multi" geometry type is provided return
 * a generic "point", "line", or "polygon" name.
 * @param geomType Geometry type from GeoJSON object.
 * @returns "Point", "Line", "Polygon", or original value.
 */
export function getGenericGeomType(geomType: string): string {
  let genericGeomType = geomType.toLowerCase();
  switch (geomType.toLowerCase()) {
    case 'multipoint':
      genericGeomType = 'point';
      break;
    case 'linestring':
      genericGeomType = 'line';
      break;
    case 'multilinestring':
      genericGeomType = 'line';
      break;
    case 'multipolygon':
      genericGeomType = 'polygon';
      break;
  }
  return genericGeomType[0].toUpperCase() + genericGeomType.slice(1);
}

function getGeomTypeIcon(geomType: string): string {
  let icon = pointIcon;
  switch (geomType.toLowerCase()) {
    case 'point':
      icon = pointIcon;
      break;
    case 'line':
      icon = lineIcon;
      break;
    case 'polygon':
      icon = polygonIcon;
      break;
  }
  return icon;
}

export default function ProjectLayersTable() {
  const { mapLayers, mapLayersDispatch, projectRole } = useProjectContext();
  const { projectId } = useParams();

  const [status, setStatus] = useState<Status | null>(null);
  const [editingLayerId, setEditingLayerId] = useState<string | null>(null);
  const [editingValue, setEditingValue] = useState<string>('');
  const [previewModalOpen, setPreviewModalOpen] = useState<boolean>(false);
  const [selectedPreview, setSelectedPreview] = useState<{
    url: string;
    name: string;
  } | null>(null);

  useInterval(() => {
    if (projectId) {
      getMapLayers(projectId, mapLayersDispatch);
    }
  }, MAP_LAYERS_POLLING_INTERVAL);

  const sortedMapLayers = useMemo(() => {
    return [...mapLayers].sort((a, b) =>
      a.layer_name.localeCompare(b.layer_name)
    );
  }, [mapLayers]);

  const handleEdit = (layer: MapLayer) => {
    setEditingLayerId(layer.layer_id);
    setEditingValue(layer.layer_name);
  };

  const handleCancel = () => {
    setEditingLayerId(null);
    setEditingValue('');
  };

  const handleSave = async (layer: MapLayer) => {
    const trimmedValue = editingValue.trim();

    // Validation: prevent empty names
    if (!trimmedValue) {
      setStatus({
        type: 'error',
        msg: 'Layer name cannot be empty',
      });
      return;
    }

    // If unchanged, just exit edit mode
    if (trimmedValue === layer.layer_name) {
      handleCancel();
      return;
    }

    if (projectId) {
      try {
        const response: AxiosResponse<MapLayerFeatureCollection> =
          await api.put(
            `/projects/${projectId}/vector_layers/${layer.layer_id}`,
            { layer_name: trimmedValue }
          );

        if (response.status === 200) {
          // Update the layer in context
          mapLayersDispatch({
            type: 'updateOne',
            payload: { ...layer, layer_name: trimmedValue },
          });
          handleCancel();
          setStatus({
            type: 'success',
            msg: 'Layer name updated successfully',
          });
        }
      } catch (err) {
        if (isAxiosError(err)) {
          setStatus({
            type: 'error',
            msg: err.response?.data.detail || 'Unable to update layer name',
          });
        } else {
          setStatus({
            type: 'error',
            msg: 'Unable to update layer name',
          });
        }
      }
    }
  };

  const handleKeyDown = (
    e: React.KeyboardEvent<HTMLInputElement>,
    layer: MapLayer
  ) => {
    if (e.key === 'Enter') {
      handleSave(layer);
    } else if (e.key === 'Escape') {
      handleCancel();
    }
  };

  const handlePreviewClick = (url: string, name: string) => {
    setSelectedPreview({ url, name });
    setPreviewModalOpen(true);
  };

  return (
    <div className="max-h-96 overflow-auto">
      <table className="relative w-full border-separate border-spacing-y-1 border-spacing-x-1">
        <thead>
          <tr className="h-12 sticky top-0 text-white bg-slate-300">
            <th scope="col" className="min-w-[100px] w-[100px]">
              Preview
            </th>
            <th scope="col" className="min-w-[180px]">
              Name
            </th>
            <th scope="col" className="min-w-[120px] w-[120px]">
              Type
            </th>
            <th scope="col" className="min-w-[280px]">
              Download
            </th>
            {projectRole !== 'viewer' && (
              <th scope="col" className="min-w-[80px] w-[80px]">
                Remove
              </th>
            )}
          </tr>
        </thead>
        <tbody>
          {sortedMapLayers.length > 0 &&
            sortedMapLayers.map((layer) => (
              <tr
                key={layer.layer_id}
                className="text-center border-2 border-slate-400"
              >
                <td className="py-2 bg-white min-w-[100px] w-[100px]">
                  {layer.preview_url ? (
                    <button
                      type="button"
                      onClick={() =>
                        handlePreviewClick(layer.preview_url, layer.layer_name)
                      }
                      className="flex items-center justify-center mx-auto cursor-pointer hover:opacity-80 transition-opacity focus:outline-hidden focus:ring-2 focus:ring-accent2 rounded-sm"
                      aria-label={`View full preview of ${layer.layer_name}`}
                      title="Click to view full size"
                    >
                      <img
                        src={layer.preview_url}
                        className="w-20 h-20 object-cover rounded-sm"
                        alt="Preview thumbnail"
                      />
                    </button>
                  ) : (
                    <div className="flex items-center justify-center w-20 h-20 mx-auto">
                      <PhotoIcon className="w-12 h-12 text-gray-400" />
                    </div>
                  )}
                </td>
                <td className="p-4 bg-white min-w-[180px]">
                  {editingLayerId === layer.layer_id ? (
                    // Edit mode
                    <div className="flex items-center gap-4">
                      <input
                        type="text"
                        value={editingValue}
                        onChange={(e) => setEditingValue(e.target.value)}
                        onKeyDown={(e) => handleKeyDown(e, layer)}
                        className="w-32 px-2 py-1 border border-gray-400 rounded-sm focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-hidden"
                        autoFocus
                      />
                      <div className="flex gap-4 shrink-0">
                        <button
                          type="button"
                          onClick={() => handleSave(layer)}
                          className="inline rounded-full focus:outline-hidden focus:ring-3 focus:ring-accent2"
                          aria-label="Save layer name"
                          title="Save"
                        >
                          <CheckIcon className="h-4 w-4 text-slate-400" />
                        </button>
                        <button
                          type="button"
                          onClick={handleCancel}
                          className="inline rounded-full focus:outline-hidden focus:ring-3 focus:ring-accent2"
                          aria-label="Cancel editing"
                          title="Cancel"
                        >
                          <XMarkIcon className="h-4 w-4 text-slate-400" />
                        </button>
                      </div>
                    </div>
                  ) : (
                    // Display mode
                    <div className="flex items-center gap-8">
                      <span className="block my-1 mx-0 truncate">
                        {layer.layer_name}
                      </span>
                      {projectRole !== 'viewer' && (
                        <button
                          type="button"
                          onClick={() => handleEdit(layer)}
                          className="shrink-0 inline rounded-full focus:outline-hidden focus:ring-3 focus:ring-accent2"
                          aria-label="Edit layer name"
                          title="Edit layer name"
                        >
                          <PencilIcon className="h-4 w-4 text-slate-400" />
                        </button>
                      )}
                    </div>
                  )}
                </td>
                <td className="p-4 bg-white min-w-[120px] w-[120px]">
                  <div className="flex items-center justify-center gap-2">
                    <img
                      src={getGeomTypeIcon(layer.geom_type)}
                      alt={`${getGenericGeomType(layer.geom_type)} icon`}
                    />
                    {layer.geom_type}
                  </div>
                </td>
                <td className="bg-white min-w-[280px] p-2">
                  <div className="flex flex-col gap-4">
                    <MapLayerDownloadLinks
                      layerId={layer.layer_id}
                      parquetUrl={layer.parquet_url}
                      fgbUrl={layer.fgb_url}
                    />
                  </div>
                </td>
                {projectRole !== 'viewer' && (
                  <td className="p-4 bg-white min-w-[80px] w-[80px]">
                    <ConfirmationModal
                      btnName="Remove map layer"
                      btnType="trashIcon"
                      iconSize={22}
                      title="Are you sure you want to remove this map layer?"
                      content="You will not be able to recover this map layer after removing it. You can always re-upload the map layer at a later time."
                      rejectText="Keep map layer"
                      confirmText="Remove map layer"
                      onConfirm={async () => {
                        if (projectId) {
                          try {
                            const response: AxiosResponse<MapLayerFeatureCollection> =
                              await api.delete(
                                `/projects/${projectId}/vector_layers/${layer.layer_id}`
                              );
                            if (response.status === 200) {
                              mapLayersDispatch({
                                type: 'remove',
                                payload: [layer],
                              });
                            } else {
                              setStatus({
                                type: 'error',
                                msg: 'Unable to remove layer',
                              });
                            }
                          } catch (err) {
                            if (isAxiosError(err)) {
                              setStatus({
                                type: 'error',
                                msg:
                                  err.response?.data.detail ||
                                  'Unable to remove layer',
                              });
                            } else {
                              setStatus({
                                type: 'error',
                                msg: 'Unable to remove layer',
                              });
                            }
                          }
                        }
                      }}
                    />
                  </td>
                )}
              </tr>
            ))}
        </tbody>
      </table>
      {status && <AlertBar alertType={status.type}>{status.msg}</AlertBar>}
      {selectedPreview && (
        <ImagePreviewModal
          open={previewModalOpen}
          setOpen={setPreviewModalOpen}
          imageUrl={selectedPreview.url}
          layerName={selectedPreview.name}
        />
      )}
    </div>
  );
}

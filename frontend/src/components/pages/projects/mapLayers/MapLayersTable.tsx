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
import { getMapLayers, useProjectContext } from '../ProjectContext';
import { AlertBar, Status } from '../../../Alert';
import { useInterval } from '../../../hooks';

import api from '../../../../api';

import pointIcon from '../../../../assets/point-icon.svg';
import lineIcon from '../../../../assets/line-icon.svg';
import polygonIcon from '../../../../assets/polygon-icon.svg';

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

  useInterval(
    () => {
      if (projectId) {
        getMapLayers(projectId, mapLayersDispatch);
      }
    },
    30000 // check every 30 seconds for new map layers
  );

  const sortedMapLayers = useMemo(() => {
    return [...mapLayers].sort((a, b) =>
      a.layer_name.localeCompare(b.layer_name)
    );
  }, [mapLayers, projectId]);

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

  return (
    <div className="max-h-96 overflow-auto">
      <table className="relative w-full border-separate border-spacing-y-1 border-spacing-x-1 table-fixed">
        <thead>
          <tr className="h-12 sticky top-0 text-white bg-slate-300">
            <th>Preview</th>
            <th className="w-64">Name</th>
            <th>Type</th>
            <th>Download</th>
            {projectRole !== 'viewer' && <th>Remove</th>}
          </tr>
        </thead>
        <tbody className="max-h-96 overflow-y-auto">
          {sortedMapLayers.length > 0 &&
            sortedMapLayers.map((layer) => (
              <tr
                key={layer.layer_id}
                className="h-48 text-center border-2 border-slate-400"
              >
                <td className="h-48 w-48 bg-white">
                  {layer.preview_url ? (
                    <div className="flex items-center justify-center">
                      <img
                        src={layer.preview_url}
                        className="w-full h-full object-cover"
                        alt="Preview image"
                      />
                    </div>
                  ) : (
                    <PhotoIcon />
                  )}
                </td>
                <td className="p-4 bg-white">
                  {editingLayerId === layer.layer_id ? (
                    // Edit mode
                    <div className="flex items-center gap-4">
                      <input
                        type="text"
                        value={editingValue}
                        onChange={(e) => setEditingValue(e.target.value)}
                        onKeyDown={(e) => handleKeyDown(e, layer)}
                        className="w-32 px-2 py-1 border border-gray-400 rounded focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none"
                        autoFocus
                      />
                      <div className="flex gap-4 flex-shrink-0">
                        <button
                          type="button"
                          onClick={() => handleSave(layer)}
                          className="inline rounded-full focus:outline-none focus:ring focus:ring-accent2"
                          title="Save"
                        >
                          <CheckIcon className="h-4 w-4 text-slate-400 cursor-pointer" />
                        </button>
                        <button
                          type="button"
                          onClick={handleCancel}
                          className="inline rounded-full focus:outline-none focus:ring focus:ring-accent2"
                          title="Cancel"
                        >
                          <XMarkIcon className="h-4 w-4 text-slate-400 cursor-pointer" />
                        </button>
                      </div>
                    </div>
                  ) : (
                    // Display mode
                    <div className="flex items-center gap-8">
                      <span className="block my-1 mx-0 truncate">{layer.layer_name}</span>
                      {projectRole !== 'viewer' && (
                        <span className="flex-shrink-0">
                          <PencilIcon
                            className="inline h-4 w-4 text-slate-400 cursor-pointer"
                            onClick={() => handleEdit(layer)}
                            title="Edit layer name"
                          />
                        </span>
                      )}
                    </div>
                  )}
                </td>
                <td className="p-4 bg-white">
                  <div className="flex items-center justify-center gap-2">
                    <img src={getGeomTypeIcon(layer.geom_type)} />
                    {layer.geom_type}
                  </div>
                </td>
                <td className="bg-white">
                  <div className="flex flex-col gap-4">
                    <MapLayerDownloadLinks layerId={layer.layer_id} />
                  </div>
                </td>
                {projectRole !== 'viewer' && (
                  <td className="p-4 bg-white">
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
                              if (isAxiosError(err)) {
                                setStatus({
                                  type: 'error',
                                  msg: err.response?.data.detail,
                                });
                              } else {
                                setStatus({
                                  type: 'error',
                                  msg: 'Unable to remove layer',
                                });
                              }
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
    </div>
  );
}

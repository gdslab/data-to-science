import axios, { AxiosResponse, isAxiosError } from 'axios';
import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { PhotoIcon } from '@heroicons/react/24/outline';

import ConfirmationModal from '../../../ConfirmationModal';
import { useProjectContext } from '../ProjectContext';
import { AlertBar, Status } from '../../../Alert';

import { download, prepMapLayers } from './utils';

import pointIcon from '../../../../assets/point-icon.svg';
import lineIcon from '../../../../assets/line-icon.svg';
import polygonIcon from '../../../../assets/polygon-icon.svg';
import { MapLayerFeatureCollection } from '../Project';

/**
 * If a "Multi" geometry type is provided return
 * a generic "point", "line", or "polygon" name.
 * @param geomType Geometry type from GeoJSON object.
 * @returns "Point", "Line", "Polygon", or original value.
 */
function getGenericGeomType(geomType: string): string {
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

  return (
    <div className="max-h-96 overflow-auto">
      <table className="relative w-full border-separate border-spacing-y-1 border-spacing-x-1">
        <thead>
          <tr className="h-12 sticky top-0 text-white bg-slate-300">
            <th>Preview</th>
            <th>Name</th>
            <th>Type</th>
            <th>Download</th>
            {projectRole !== 'viewer' && <th>Remove</th>}
          </tr>
        </thead>
        <tbody className="max-h-96 overflow-y-auto">
          {mapLayers &&
            prepMapLayers(mapLayers).map((layer) => (
              <tr key={layer.id} className="h-48 text-center border-2 border-slate-400">
                <td className="h-48 w-48 bg-white">
                  {layer.featureCollection.features[0].properties ? (
                    <img
                      src={layer.featureCollection.metadata.preview_url}
                      className="w-full h-full object-cover"
                      alt="Preview image"
                    />
                  ) : (
                    <PhotoIcon />
                  )}
                </td>
                <td className="p-4 bg-white">{layer.name}</td>
                <td className="p-4 bg-white">
                  <div className="flex items-center justify-center gap-2">
                    <img src={getGeomTypeIcon(getGenericGeomType(layer.geomType))} />
                    {getGenericGeomType(layer.geomType)}
                  </div>
                </td>
                <td className="bg-white">
                  <div className="flex flex-col gap-4">
                    <div className="flex items-center justify-center bg-white">
                      <button
                        className="flex items-center gap-1"
                        type="button"
                        onClick={() => download('json', layer.featureCollection)}
                      >
                        <span className="text-sky-600">GeoJSON</span>
                      </button>
                    </div>
                    <div className="flex items-center justify-center bg-white">
                      <button
                        className="flex items-center gap-1"
                        type="button"
                        onClick={() => download('zip', layer.featureCollection)}
                      >
                        <span className="text-sky-600">Shapefile</span>
                      </button>
                    </div>
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
                              await axios.delete(
                                `${
                                  import.meta.env.VITE_API_V1_STR
                                }/projects/${projectId}/vector_layers/${layer.id}`
                              );
                            if (response.status === 200) {
                              // update map layer context with new map layer
                              mapLayersDispatch({
                                type: 'remove',
                                payload: [response.data],
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

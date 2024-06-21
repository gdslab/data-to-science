import axios, { AxiosResponse, isAxiosError } from 'axios';
import { FeatureCollection } from 'geojson';
import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { ArrowDownTrayIcon } from '@heroicons/react/24/outline';

import ConfirmationModal from '../../../ConfirmationModal';
import { useProjectContext } from '../ProjectContext';
import { AlertBar, Status } from '../../../Alert';

import { download, prepMapLayers } from './utils';

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
    case 'multilinestring':
      genericGeomType = 'line';
      break;
    case 'multipolygon':
      genericGeomType = 'polygon';
      break;
  }
  return genericGeomType[0].toUpperCase() + genericGeomType.slice(1);
}

export default function ProjectLayersTable() {
  const { mapLayers, mapLayersDispatch } = useProjectContext();
  const { projectId } = useParams();

  const [status, setStatus] = useState<Status | null>(null);

  return (
    <div>
      <table className="table-auto border-separate border-spacing-1">
        <thead>
          <tr className="text-slate-600">
            <th>Preview</th>
            <th>Name</th>
            <th>Type</th>
            <th>Download</th>
            <th>Remove</th>
          </tr>
        </thead>
        <tbody>
          {mapLayers &&
            prepMapLayers(mapLayers).map((layer) => (
              <tr key={layer.id}>
                <td className="p-4 bg-white"></td>
                <td className="p-4 bg-white">{layer.name}</td>
                <td className="p-4 bg-white">{getGenericGeomType(layer.geomType)}</td>
                <td className="p-4 bg-white">
                  <div className="flex items-center justify-between gap-4">
                    <button
                      className="flex items-center gap-1"
                      type="button"
                      onClick={() => download('json', layer.featureCollection)}
                    >
                      <ArrowDownTrayIcon className="h-4 w-4" />
                      <span className="text-sky-600">GeoJSON</span>
                    </button>
                    <button
                      className="flex items-center gap-1"
                      type="button"
                      onClick={() => download('zip', layer.featureCollection)}
                    >
                      <ArrowDownTrayIcon className="h-4 w-4" />
                      <span className="text-sky-600">Shapefile</span>
                    </button>
                  </div>
                </td>
                <td className="p-4 bg-white">
                  <ConfirmationModal
                    btnName="Remove map layer"
                    btnType="trashIcon"
                    title="Are you sure you want to remove this map layer?"
                    content="You will not be able to recover this map layer after removing it. You can always re-upload the map layer at a later time."
                    rejectText="Keep map layer"
                    confirmText="Remove map layer"
                    onConfirm={async () => {
                      if (projectId) {
                        try {
                          const response: AxiosResponse<FeatureCollection> =
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
              </tr>
            ))}
        </tbody>
      </table>
      {status && <AlertBar alertType={status.type}>{status.msg}</AlertBar>}
    </div>
  );
}

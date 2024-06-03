import { useProjectContext } from '../ProjectContext';

import { download, prepMapLayers } from './utils';

export default function ProjectLayersTable() {
  const { mapLayers } = useProjectContext();

  return (
    <div>
      <h3>Layers</h3>
      <table className="table-auto border-separate border-spacing-1">
        <thead>
          <tr className="text-slate-600">
            <th>Name</th>
            <th>Type</th>
            <th>Download</th>
          </tr>
        </thead>
        <tbody>
          {mapLayers &&
            prepMapLayers(mapLayers).map((layer) => (
              <tr key={layer.id}>
                <td className="p-4 bg-white">{layer.name}</td>
                <td className="p-4 bg-white">{layer.geomType}</td>
                <td className="p-4 bg-white">
                  <div className="flex items-center justify-center gap-4">
                    <button
                      type="button"
                      onClick={() => download('json', layer.featureCollection)}
                    >
                      <span className="text-sky-600">GeoJSON</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => download('zip', layer.featureCollection)}
                    >
                      <span className="text-sky-600">Shapefile</span>
                    </button>
                  </div>
                </td>
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  );
}

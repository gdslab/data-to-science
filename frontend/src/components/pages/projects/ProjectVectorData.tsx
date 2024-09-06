import { useProjectContext } from './ProjectContext';
import MapLayerUpload from './mapLayers/MapLayerUpload';
import MapLayersTable from './mapLayers/MapLayersTable';

export default function ProjectVectorData() {
  const { mapLayers, projectRole } = useProjectContext();

  return (
    <div className="mb-4">
      <h2>Map Layers</h2>
      <div className="flex flex-col gap-4">
        {mapLayers.length > 0 && <MapLayersTable />}
        {mapLayers.length === 0 &&
          (projectRole !== 'viewer' ? (
            <span>Use the below button to add your first map layer.</span>
          ) : (
            <span>No map layers have been added.</span>
          ))}
        {projectRole !== 'viewer' ? <MapLayerUpload /> : null}
      </div>
    </div>
  );
}

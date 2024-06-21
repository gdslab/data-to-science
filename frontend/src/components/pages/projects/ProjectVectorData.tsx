import MapLayerUpload from './mapLayers/MapLayerUpload';
import MapLayersTable from './mapLayers/MapLayersTable';

export default function ProjectVectorData() {
  return (
    <div>
      <h2>Map Layers</h2>
      <div className="flex flex-col gap-4">
        <MapLayersTable />
        <MapLayerUpload />
      </div>
    </div>
  );
}

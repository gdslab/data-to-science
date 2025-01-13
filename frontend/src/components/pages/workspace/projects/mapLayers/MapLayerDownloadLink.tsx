import { useParams } from 'react-router-dom';

export default function MapLayerDownloadLinks({ layerId }: { layerId: string }) {
  const { projectId } = useParams();

  return (
    <div className="flex flex-col gap-2">
      <a
        href={`${
          import.meta.env.VITE_API_V1_STR
        }/projects/${projectId}/vector_layers/${layerId}/download?format=json`}
        download
      >
        <span className="text-sky-600">GeoJSON</span>
      </a>
      <a
        href={`${
          import.meta.env.VITE_API_V1_STR
        }/projects/${projectId}/vector_layers/${layerId}/download?format=shp`}
        download
      >
        <span className="text-sky-600">Shapefile</span>
      </a>
    </div>
  );
}

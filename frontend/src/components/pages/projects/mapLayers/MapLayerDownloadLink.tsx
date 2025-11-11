import { useParams } from 'react-router-dom';

interface MapLayerDownloadLinksProps {
  layerId: string;
  layerName: string;
}

export default function MapLayerDownloadLinks({
  layerId,
  layerName,
}: MapLayerDownloadLinksProps) {
  const { projectId } = useParams();

  const parquetUrl = `/static/projects/${projectId}/vector/${layerId}/${layerId}.parquet`;
  const flatgeobufUrl = `/static/projects/${projectId}/vector/${layerId}/${layerId}.fgb`;

  return (
    <div className="flex flex-row items-center justify-center gap-2">
      <a
        href={`${
          import.meta.env.VITE_API_V1_STR
        }/projects/${projectId}/vector_layers/${layerId}/download?format=json`}
        download={`${layerId}.geojson`}
        className="text-sky-600 hover:text-sky-800 hover:underline"
      >
        GeoJSON
      </a>
      <span className="text-gray-400">|</span>
      <a
        href={`${
          import.meta.env.VITE_API_V1_STR
        }/projects/${projectId}/vector_layers/${layerId}/download?format=shp`}
        download={`${layerId}.zip`}
        className="text-sky-600 hover:text-sky-800 hover:underline"
      >
        Shapefile
      </a>
      <span className="text-gray-400">|</span>
      <a
        href={parquetUrl}
        download={`${layerId}.parquet`}
        className="text-sky-600 hover:text-sky-800 hover:underline"
      >
        GeoParquet
      </a>
      <span className="text-gray-400">|</span>
      <a
        href={flatgeobufUrl}
        download={`${layerId}.fgb`}
        className="text-sky-600 hover:text-sky-800 hover:underline"
      >
        FlatGeobuf
      </a>
    </div>
  );
}

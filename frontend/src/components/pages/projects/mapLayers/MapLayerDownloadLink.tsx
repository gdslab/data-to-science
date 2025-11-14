import { useParams } from 'react-router-dom';

interface MapLayerDownloadLinksProps {
  layerId: string;
  parquetUrl: string;
  fgbUrl: string;
}

export default function MapLayerDownloadLinks({
  layerId,
  parquetUrl,
  fgbUrl,
}: MapLayerDownloadLinksProps) {
  const { projectId } = useParams();

  return (
    <div className="flex flex-row flex-wrap items-center justify-center gap-x-2 gap-y-1">
      <a
        href={`${
          import.meta.env.VITE_API_V1_STR
        }/projects/${projectId}/vector_layers/${layerId}/download?format=json`}
        download={`${layerId}.geojson`}
        className="text-sky-600 hover:text-sky-800 hover:underline whitespace-nowrap"
      >
        GeoJSON
      </a>
      <span className="text-gray-400">|</span>
      <a
        href={`${
          import.meta.env.VITE_API_V1_STR
        }/projects/${projectId}/vector_layers/${layerId}/download?format=shp`}
        download={`${layerId}.zip`}
        className="text-sky-600 hover:text-sky-800 hover:underline whitespace-nowrap"
      >
        Shapefile
      </a>
      <span className="text-gray-400">|</span>
      <a
        href={parquetUrl}
        download={`${layerId}.parquet`}
        className="text-sky-600 hover:text-sky-800 hover:underline whitespace-nowrap"
      >
        GeoParquet
      </a>
      <span className="text-gray-400">|</span>
      <a
        href={fgbUrl}
        download={`${layerId}.fgb`}
        className="text-sky-600 hover:text-sky-800 hover:underline whitespace-nowrap"
      >
        FlatGeobuf
      </a>
    </div>
  );
}

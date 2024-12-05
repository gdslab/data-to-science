import { useMapContext } from './MapContext';
import MaplibreCompareMap from './MaplibreCompareMap';
import MaplibreMap from './MaplibreMap';

export default function MaplibreView() {
  const { activeMapTool } = useMapContext();

  if (activeMapTool === 'compare') {
    return <MaplibreCompareMap />;
  } else {
    return <MaplibreMap />;
  }
}

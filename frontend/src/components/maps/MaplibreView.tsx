import { useMapContext } from './MapContext';
import MaplibreCompareMap from './MaplibreCompareMap';
import MaplibreMap from './MaplibreMap';
import PotreeViewer from './PotreeViewer';

export default function MaplibreView() {
  const { activeDataProduct, activeMapTool } = useMapContext();

  if (activeMapTool === 'compare') {
    return <MaplibreCompareMap />;
  } else if (
    !activeDataProduct ||
    (activeDataProduct && activeDataProduct.data_type !== 'point_cloud')
  ) {
    return <MaplibreMap />;
  } else {
    const copcPath = activeDataProduct.url;
    return <PotreeViewer copcPath={copcPath} />;
  }
}

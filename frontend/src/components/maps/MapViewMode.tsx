import { useMapContext } from './MapContext';
import CompareMap from './CompareMap';
import HomeMap from './HomeMap';
import PotreeViewer from './PotreeViewer';

export default function MapViewMode() {
  const { activeDataProduct, activeMapTool } = useMapContext();

  if (activeMapTool === 'compare') {
    return <CompareMap />;
  } else if (
    !activeDataProduct ||
    (activeDataProduct && activeDataProduct.data_type !== 'point_cloud')
  ) {
    return <HomeMap />;
  } else {
    const copcPath = activeDataProduct.url;
    return <PotreeViewer copcPath={copcPath} />;
  }
}

import { PlantDetailAndChart } from '../types';
import PotGroupModuleDataVisualization from '../../PotGroupModule/PotGroupModuleDataVisualization';

export default function TopChart({ data }: { data: PlantDetailAndChart }) {
  const indoorProjectPlant = data;
  const topImages: Record<string, string[]> = indoorProjectPlant.top.reduce(
    (acc, { dfp, images }) => ({
      ...acc,
      [dfp]: images,
    }),
    {}
  );
  return (
    <PotGroupModuleDataVisualization
      data={indoorProjectPlant.topChart}
      images={topImages}
    />
  );
}

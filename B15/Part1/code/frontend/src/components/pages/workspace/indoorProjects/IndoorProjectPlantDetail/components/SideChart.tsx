import { PlantDetailAndChart } from '../types';
import PotGroupModuleDataVisualization from '../../PotGroupModule/PotGroupModuleDataVisualization';

export default function SideChart({ data }: { data: PlantDetailAndChart }) {
  const indoorProjectPlant = data;
  const sideImages: Record<string, string[]> =
    indoorProjectPlant.side_avg.reduce(
      (acc, { dfp, images }) => ({
        ...acc,
        [dfp]: images,
      }),
      {}
    );
  return (
    <PotGroupModuleDataVisualization
      data={indoorProjectPlant.sideChart}
      images={sideImages}
    />
  );
}

import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';
import { PlantDetailAndChart } from '../types';
import TraitScatterModuleDataVisualization from '../../TraitModule/TraitScatterModuleDataVisualization';
import { fetchTraitScatterModuleVisualizationData } from '../../TraitModule/scatterService';
import { IndoorProjectDataVizScatterAPIResponse } from '../../IndoorProject';

export default function TraitScatterSection({
  data,
}: {
  data: PlantDetailAndChart;
}) {
  const indoorProjectPlant = data;
  const { indoorProjectId, indoorProjectDataId, indoorProjectPlantId } =
    useParams();

  const [cameraOrientation, setCameraOrientation] = useState<'top' | 'side'>(
    'top'
  );
  const [traitX, setTraitX] = useState<string>('');
  const [traitY, setTraitY] = useState<string>('');
  const [isSubmittingScatter, setIsSubmittingScatter] = useState(false);
  const [scatterData, setScatterData] =
    useState<IndoorProjectDataVizScatterAPIResponse | null>(null);

  const availableTraits = useMemo(() => {
    return cameraOrientation === 'top'
      ? indoorProjectPlant.numericColumns.top
      : indoorProjectPlant.numericColumns.side;
  }, [cameraOrientation, indoorProjectPlant.numericColumns]);

  useEffect(() => {
    if (availableTraits.length > 1) {
      setTraitX((prev) => prev || availableTraits[0]);
      setTraitY((prev) => prev || availableTraits[1]);
    } else if (availableTraits.length === 1) {
      setTraitX((prev) => prev || availableTraits[0]);
      setTraitY((prev) => prev || availableTraits[0]);
    }
  }, [availableTraits]);

  async function handleGenerateScatter(e: React.FormEvent) {
    e.preventDefault();
    if (
      !indoorProjectId ||
      !indoorProjectDataId ||
      !traitX ||
      !traitY ||
      !indoorProjectPlantId
    )
      return;

    try {
      setIsSubmittingScatter(true);
      const data = await fetchTraitScatterModuleVisualizationData({
        indoorProjectId,
        indoorProjectDataId,
        cameraOrientation,
        plottedBy: 'pots',
        accordingTo: 'single_pot',
        targetTraitX: traitX,
        targetTraitY: traitY,
        potBarcode: Number(indoorProjectPlantId),
      });

      setScatterData(data);
    } catch (err) {
      console.error('Failed to generate scatter plot', err);
      setScatterData(null);
    } finally {
      setIsSubmittingScatter(false);
    }
  }

  return (
    <div>
      <h2>Trait scatter (single plant)</h2>
      <form className="flex flex-col gap-3" onSubmit={handleGenerateScatter}>
        <div className="flex gap-4 items-center">
          <label className="flex items-center gap-2">
            <input
              type="radio"
              name="cameraOrientation"
              value="top"
              checked={cameraOrientation === 'top'}
              onChange={() => setCameraOrientation('top')}
            />
            <span>Top</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="radio"
              name="cameraOrientation"
              value="side"
              checked={cameraOrientation === 'side'}
              onChange={() => setCameraOrientation('side')}
            />
            <span>Side</span>
          </label>
        </div>
        <div className="flex gap-4 flex-wrap">
          <label className="flex flex-col gap-1 min-w-56">
            <span>X trait</span>
            <select
              className="p-2 rounded border border-gray-300"
              value={traitX}
              onChange={(e) => setTraitX(e.target.value)}
            >
              {availableTraits.map((t) => (
                <option key={`x-${t}`} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 min-w-56">
            <span>Y trait</span>
            <select
              className="p-2 rounded border border-gray-300"
              value={traitY}
              onChange={(e) => setTraitY(e.target.value)}
            >
              {availableTraits.map((t) => (
                <option key={`y-${t}`} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div>
          <button
            type="submit"
            disabled={isSubmittingScatter || availableTraits.length < 2}
            className="px-4 py-2 bg-blue-500 text-white font-medium rounded hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-300 disabled:bg-blue-500/60 disabled:cursor-not-allowed"
          >
            {isSubmittingScatter ? 'Generating...' : 'Generate scatter'}
          </button>
        </div>
      </form>
      {scatterData && scatterData.results.length > 0 && (
        <div className="mt-4">
          <TraitScatterModuleDataVisualization data={scatterData} />
        </div>
      )}
    </div>
  );
}

import CollectionPreview from '../CollectionPreview';
import ProcessingSummary from '../ProcessingSummary';
import ItemsList from '../ItemsList';
import { STACMetadata, CombinedSTACItem } from '../STACTypes';
import { Project } from '../../Project';

interface STACPreviewPanelProps {
  stacMetadata: STACMetadata;
  allItems: CombinedSTACItem[];
  project: Project;
}

export default function STACPreviewPanel({
  stacMetadata,
  allItems,
  project,
}: STACPreviewPanelProps) {
  return (
    <div className="lg:col-span-1 mt-8 lg:mt-0">
      <h3 className="text-md font-bold mb-4">Metadata Preview</h3>
      <div className="bg-gray-50 p-4 rounded-lg">
        <CollectionPreview stacMetadata={stacMetadata} project={project} />
        <ProcessingSummary allItems={allItems} />
        <ItemsList allItems={allItems} project={project} />
      </div>
    </div>
  );
}

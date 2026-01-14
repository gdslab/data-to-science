import CollectionPreview from '../CollectionPreview';
import ProcessingSummary from '../ProcessingSummary';
import ItemsList from '../ItemsList';
import { STACMetadata, CombinedSTACItem } from '../STACTypes';
import { ProjectDetail } from '../../Project';

interface STACPreviewPanelProps {
  stacMetadata: STACMetadata;
  allItems: CombinedSTACItem[];
  project: ProjectDetail;
  includeRawDataLinks: Set<string>;
  onToggleRawDataLink: (itemId: string) => void;
  onToggleAllRawDataLinks: () => void;
}

export default function STACPreviewPanel({
  stacMetadata,
  allItems,
  project,
  includeRawDataLinks,
  onToggleRawDataLink,
  onToggleAllRawDataLinks,
}: STACPreviewPanelProps) {
  return (
    <div className="lg:col-span-1 mt-8 lg:mt-0">
      <h3 className="text-md font-bold mb-4">Metadata Preview</h3>
      <div className="bg-gray-50 p-4 rounded-lg">
        <CollectionPreview stacMetadata={stacMetadata} project={project} />
        <ProcessingSummary allItems={allItems} />
        <ItemsList
          allItems={allItems}
          project={project}
          includeRawDataLinks={includeRawDataLinks}
          onToggleRawDataLink={onToggleRawDataLink}
          onToggleAllRawDataLinks={onToggleAllRawDataLinks}
        />
      </div>
    </div>
  );
}

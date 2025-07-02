import CollectionPreview from '../CollectionPreview';
import ProcessingSummary from '../ProcessingSummary';
import ItemsList from '../ItemsList';
import { STACMetadata, CombinedSTACItem } from '../STACTypes';

interface STACPreviewPanelProps {
  stacMetadata: STACMetadata;
  allItems: CombinedSTACItem[];
}

export default function STACPreviewPanel({
  stacMetadata,
  allItems,
}: STACPreviewPanelProps) {
  return (
    <div className="lg:col-span-1 mt-8 lg:mt-0">
      <h3 className="text-md font-bold mb-4">Metadata Preview</h3>
      <div className="bg-gray-50 p-4 rounded-lg">
        <CollectionPreview stacMetadata={stacMetadata} />
        <ProcessingSummary allItems={allItems} />
        <ItemsList allItems={allItems} />
      </div>
    </div>
  );
}

import { STACItem } from './STACTypes';

interface STACItemTitlesFormProps {
  items: STACItem[];
  customTitles: Record<string, string>;
  setCustomTitles: (titles: Record<string, string>) => void;
}

export default function STACItemTitlesForm({
  items,
  customTitles,
  setCustomTitles,
}: STACItemTitlesFormProps) {
  const generateDefaultTitle = (item: STACItem) => {
    const acquisitionDate = new Date(
      item.properties.flight_details.acquisition_date
    )
      .toISOString()
      .split('T')[0];
    const dataType = item.properties.data_product_details.data_type;
    const sensor = item.properties.flight_details.sensor;
    const platform = item.properties.flight_details.platform;
    return `${acquisitionDate}_${dataType}_${sensor}_${platform}`;
  };

  const handleTitleChange = (itemId: string, title: string) => {
    setCustomTitles({
      ...customTitles,
      [itemId]: title,
    });
  };

  const clearCustomTitle = (itemId: string) => {
    // Find the item to generate its default title
    const item = items.find((item) => item.id === itemId);
    if (!item) return;

    // Generate the actual default title
    const defaultTitle = generateDefaultTitle(item);

    // Set the title to the generated default instead of deleting
    // This ensures it will override any server-stored custom title
    setCustomTitles({
      ...customTitles,
      [itemId]: defaultTitle,
    });
  };

  return (
    <div className="mb-6 bg-gray-50 p-4 rounded-lg">
      <h3 className="text-md font-semibold mb-3">Item Titles (Optional)</h3>
      <p className="text-sm text-gray-600 mb-4">
        Customize the titles for your STAC items. Leave blank to use the default
        generated title.
      </p>
      <div className="space-y-4 max-h-96 overflow-y-auto">
        {items.map((item) => {
          const defaultTitle = generateDefaultTitle(item);
          const localCustomTitle = customTitles[item.id] || '';

          // If no local custom title but item has a title that differs from default,
          // show the item's title in the input field
          const displayTitle =
            localCustomTitle ||
            (item.properties.title && item.properties.title !== defaultTitle
              ? item.properties.title
              : '');

          return (
            <div
              key={item.id}
              className="border border-gray-200 rounded-lg p-3 bg-white"
            >
              <div className="mb-2">
                <p className="text-sm font-medium text-gray-700">
                  Item ID: {item.id}
                </p>
                <p className="text-xs text-gray-500">
                  {item.properties.data_product_details.data_type} •{' '}
                  {
                    new Date(item.properties.flight_details.acquisition_date)
                      .toISOString()
                      .split('T')[0]
                  }{' '}
                  {item.properties.flight_details.flight_name && (
                    <>• {item.properties.flight_details.flight_name} </>
                  )}
                  • {item.properties.flight_details.sensor} •{' '}
                  {item.properties.flight_details.platform.replace(/_/g, ' ')}
                </p>
              </div>

              <div className="mb-2">
                <label
                  htmlFor={`title-${item.id}`}
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Custom Title
                </label>
                <input
                  id={`title-${item.id}`}
                  type="text"
                  value={displayTitle}
                  onChange={(e) => handleTitleChange(item.id, e.target.value)}
                  placeholder={defaultTitle}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-xs focus:outline-hidden focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                {displayTitle && (
                  <button
                    type="button"
                    onClick={() => clearCustomTitle(item.id)}
                    className="mt-1 text-xs text-blue-600 hover:text-blue-800 underline cursor-pointer"
                  >
                    Reset to default
                  </button>
                )}
              </div>

              <div className="text-xs text-gray-500">
                <span className="font-medium">Default title:</span>{' '}
                {defaultTitle}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

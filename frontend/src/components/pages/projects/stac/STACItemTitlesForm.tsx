interface STACItem {
  id: string;
  type: string;
  properties: {
    title?: string;
    datetime: string;
    data_product_details: {
      data_type: string;
    };
    flight_details: {
      acquisition_date: string;
      platform: string;
      sensor: string;
    };
  };
  browser_url?: string;
}

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
    const platform = item.properties.flight_details.platform.replace(/_/g, ' ');
    return `${acquisitionDate}_${dataType}_${sensor}_${platform}`;
  };

  const handleTitleChange = (itemId: string, title: string) => {
    setCustomTitles({
      ...customTitles,
      [itemId]: title,
    });
  };

  const clearCustomTitle = (itemId: string) => {
    const newTitles = { ...customTitles };
    delete newTitles[itemId];
    setCustomTitles(newTitles);
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
          const customTitle = customTitles[item.id] || '';

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
                  {new Date(
                    item.properties.flight_details.acquisition_date
                  ).toLocaleDateString()}{' '}
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
                  value={customTitle}
                  onChange={(e) => handleTitleChange(item.id, e.target.value)}
                  placeholder={defaultTitle}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                {customTitle && (
                  <button
                    type="button"
                    onClick={() => clearCustomTitle(item.id)}
                    className="mt-1 text-xs text-blue-600 hover:text-blue-800 underline"
                  >
                    Clear (use default)
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

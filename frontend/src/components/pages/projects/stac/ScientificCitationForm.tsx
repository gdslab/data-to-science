interface ScientificCitationFormProps {
  sciDoi: string;
  setSciDoi: (value: string) => void;
  sciCitation: string;
  setSciCitation: (value: string) => void;
}

export default function ScientificCitationForm({
  sciDoi,
  setSciDoi,
  sciCitation,
  setSciCitation,
}: ScientificCitationFormProps) {
  return (
    <div className="mb-6 bg-gray-50 p-4 rounded-lg">
      <h3 className="text-md font-semibold mb-3">
        Scientific Citation (Optional)
      </h3>
      <div className="space-y-4">
        <div>
          <label
            htmlFor="sci-doi"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            DOI
          </label>
          <input
            id="sci-doi"
            type="text"
            value={sciDoi}
            onChange={(e) => setSciDoi(e.target.value)}
            placeholder="e.g., 10.1000/xyz123"
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          <p className="text-xs text-gray-500 mt-1">
            Digital Object Identifier (without the doi: prefix or URL)
          </p>
        </div>
        <div>
          <label
            htmlFor="sci-citation"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Citation
          </label>
          <textarea
            id="sci-citation"
            value={sciCitation}
            onChange={(e) => setSciCitation(e.target.value)}
            placeholder="e.g., Smith, J., et al. (2023). Title of the dataset. Journal Name, 1(1), 1-10."
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          <p className="text-xs text-gray-500 mt-1">
            Human-readable citation for the data
          </p>
        </div>
      </div>
    </div>
  );
}

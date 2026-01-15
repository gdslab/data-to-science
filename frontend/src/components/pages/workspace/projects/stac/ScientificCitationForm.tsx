import licensesData from './licenses.json';

interface ScientificCitationFormProps {
  sciDoi: string;
  setSciDoi: (value: string) => void;
  sciCitation: string;
  setSciCitation: (value: string) => void;
  license: string;
  setLicense: (value: string) => void;
}

export default function ScientificCitationForm({
  sciDoi,
  setSciDoi,
  sciCitation,
  setSciCitation,
  license,
  setLicense,
}: ScientificCitationFormProps) {
  // Filter licenses to only include the specified IDs
  const allowedLicenseIds = [
    'MIT',
    'ISC',
    'Unlicense',
    'GPL-2.0',
    'GPL-3.0',
    'CC0-1.0',
    'CC-BY-4.0',
    'CC-BY-SA-4.0',
    'CC-BY-NC-4.0',
    'CC-BY-ND-4.0',
  ];

  const availableLicenses = licensesData.licenses
    .filter((license) => allowedLicenseIds.includes(license.licenseId))
    .sort((a, b) => a.name.localeCompare(b.name));

  const selectedLicense = availableLicenses.find(
    (l) => l.licenseId === license
  );

  return (
    <div className="mb-6 bg-gray-50 p-4 rounded-lg">
      <h3 className="text-md font-semibold mb-3">
        Scientific Citation & Licensing
      </h3>
      <div className="space-y-4">
        {/* License Selection - Required */}
        <div>
          <label
            htmlFor="license"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            License <span className="text-red-500">*</span>
          </label>
          <div className="flex items-center space-x-2">
            <select
              id="license"
              value={license}
              onChange={(e) => setLicense(e.target.value)}
              required
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-xs focus:outline-hidden focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Select a license...</option>
              {availableLicenses.map((licenseOption) => (
                <option
                  key={licenseOption.licenseId}
                  value={licenseOption.licenseId}
                >
                  {licenseOption.name}
                </option>
              ))}
            </select>
            {selectedLicense && (
              <a
                href={selectedLicense.reference}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800 text-sm underline whitespace-nowrap"
              >
                View License
              </a>
            )}
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Choose the license under which your data will be made available
          </p>
        </div>

        {/* DOI - Optional */}
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
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-xs focus:outline-hidden focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          <p className="text-xs text-gray-500 mt-1">
            Digital Object Identifier (without the doi: prefix or URL)
          </p>
        </div>

        {/* Citation - Optional */}
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
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-xs focus:outline-hidden focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          <p className="text-xs text-gray-500 mt-1">
            Human-readable citation for the data
          </p>
        </div>
      </div>
    </div>
  );
}

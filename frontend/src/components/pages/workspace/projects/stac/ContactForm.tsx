interface ContactFormProps {
  name: string;
  setName: (value: string) => void;
  email: string;
  setEmail: (value: string) => void;
  projectOwnerName?: string;
  projectOwnerEmail?: string;
}

export default function ContactForm({
  name,
  setName,
  email,
  setEmail,
  projectOwnerName,
  projectOwnerEmail,
}: ContactFormProps) {
  const handlePopulateOwner = () => {
    if (projectOwnerName) setName(projectOwnerName);
    if (projectOwnerEmail) setEmail(projectOwnerEmail);
  };

  return (
    <div className="mb-6 bg-gray-50 p-4 rounded-lg">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-md font-semibold">Contact Information</h3>
        {projectOwnerName && projectOwnerEmail && (
          <button
            type="button"
            onClick={handlePopulateOwner}
            className="text-sm text-blue-600 hover:text-blue-800 underline"
          >
            Populate with project owner
          </button>
        )}
      </div>
      <div className="space-y-4">
        {/* Name and Email - Same Row on larger screens */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label
              htmlFor="contact-name"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Name
            </label>
            <input
              id="contact-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter contact name"
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-xs focus:outline-hidden focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label
              htmlFor="contact-email"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Contact email
            </label>
            <input
              id="contact-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter contact email"
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-xs focus:outline-hidden focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      </div>
    </div>
  );
}

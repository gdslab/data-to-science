import { DataProduct, Flight } from '../pages/projects/ProjectDetail';
import { Project } from '../pages/projects/ProjectList';

export default function FlightControl({
  activeDataProduct,
  colorRamp,
  flights,
  project,
  setActiveDataProduct,
  setColorRamp,
}: {
  activeDataProduct: DataProduct | null;
  colorRamp: string;
  flights: Flight[];
  project: Project;
  setActiveDataProduct: React.Dispatch<React.SetStateAction<DataProduct | null>>;
  setColorRamp: React.Dispatch<React.SetStateAction<string>>;
}) {
  return (
    <div className="leaflet-control-container">
      <div className="leaflet-top leaflet-right top-24 mr-2.5">
        <div className="leaflet-control w-96">
          <article className="rounded-lg border border-gray-100 bg-white p-4 shadow-sm transition hover:shadow-lg sm:p-6">
            <h3>{project.title}</h3>
            <p className="mt-2 line-clamp-3 text-sm/relaxed text-gray-500">
              {project.description}
            </p>
            <hr className="mb-4 border-gray-700" />
            {flights.length > 0 ? (
              flights.map((flight) => (
                <div key={flight.id} className="mb-4">
                  <h4>
                    {new Date(flight.acquisition_date).toISOString().split('T')[0]}
                  </h4>
                  <fieldset className="space-y-4">
                    <legend className="sr-only">Data Products</legend>
                    {flight.data_products && flight.data_products.length > 0 ? (
                      flight.data_products.map((data_product) => (
                        <div key={data_product.id}>
                          <input
                            type="radio"
                            name="DataProductOption"
                            value={data_product.id}
                            id={`DataProduct-${data_product.id}`}
                            className="peer hidden [&:checked_+_label_svg]:block"
                            checked={
                              activeDataProduct !== null &&
                              activeDataProduct.id === data_product.id
                            }
                            onChange={() => {
                              setActiveDataProduct(data_product);
                            }}
                          />

                          <label
                            htmlFor={`DataProduct-${data_product.id}`}
                            className="flex cursor-pointer items-center justify-between rounded-lg border border-gray-100 bg-white p-4 text-sm font-medium shadow-sm hover:border-gray-200 peer-checked:border-blue-500 peer-checked:ring-1 peer-checked:ring-blue-500"
                          >
                            <div className="flex items-center gap-2">
                              <svg
                                className="hidden h-5 w-5 text-blue-600"
                                xmlns="http://www.w3.org/2000/svg"
                                viewBox="0 0 20 20"
                                fill="currentColor"
                              >
                                <path
                                  fillRule="evenodd"
                                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                                  clipRule="evenodd"
                                />
                              </svg>

                              <p className="text-gray-700 text-ellipsis">
                                {data_product.data_type.toUpperCase()}
                              </p>
                            </div>
                          </label>
                        </div>
                      ))
                    ) : (
                      <span>No data products for flight</span>
                    )}
                  </fieldset>
                  {activeDataProduct &&
                  activeDataProduct.stac_properties.raster.length === 1 ? (
                    <div>
                      <label
                        htmlFor="colorRamp"
                        className="block text-sm font-medium text-gray-900"
                      >
                        Color Ramp
                      </label>

                      <select
                        name="colorRamp"
                        id="colorRamp"
                        className="mt-1.5 w-full rounded-lg border-gray-300 text-gray-700 sm:text-sm"
                        value={colorRamp}
                        onChange={(e) => setColorRamp(e.target.value)}
                      >
                        <option value="spectral">Spectral</option>
                        <option value="rdylbu">Red/Yellow/Blue</option>
                        <option value="ylgn">Yellow/Green</option>
                      </select>
                    </div>
                  ) : null}
                </div>
              ))
            ) : (
              <span>No flights for project</span>
            )}
          </article>
        </div>
      </div>
    </div>
  );
}

import {
  ArrowUturnLeftIcon,
  Bars3Icon,
  MapIcon,
  MapPinIcon,
  PaperAirplaneIcon,
  PhotoIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';

import { DataProduct } from '../pages/projects/ProjectDetail';
import { Project } from '../pages/projects/ProjectList';
import { useMapContext } from './MapContext';
import HintText from '../HintText';
import { Button } from '../Buttons';
import { Link } from 'react-router-dom';

function classNames(...classes: [string, string]) {
  return classes.filter(Boolean).join(' ');
}

function LayerCard({
  children,
  dataProduct = undefined,
  hover = false,
  project = undefined,
}: {
  children: React.ReactNode;
  dataProduct?: DataProduct;
  hover?: boolean;
  project?: Project;
}) {
  const {
    activeProjectDispatch,
    activeDataProductDispatch,
    projectHoverStateDispatch,
  } = useMapContext();
  return (
    <div
      className={classNames(
        hover ? 'cursor-pointer hover:border-2 hover:border-accent1' : '',
        'p-2 rounded-sm drop-shadow-sm bg-white border-solid border-2 border-slate-200'
      )}
      onClick={() => {
        if (project) activeProjectDispatch({ type: 'set', payload: project });
        if (dataProduct)
          activeDataProductDispatch({ type: 'set', payload: dataProduct });
      }}
      onMouseOver={() => {
        if (project) projectHoverStateDispatch({ type: 'set', payload: project.id });
      }}
      onMouseLeave={() => {
        projectHoverStateDispatch({ type: 'clear', payload: null });
      }}
    >
      {children}
    </div>
  );
}

function formatDate(datestring) {
  return new Date(datestring).toLocaleDateString('en-us', {
    timeZone: 'UTC',
    weekday: 'long',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export default function LayerPane({
  hidePane,
  projects,
  toggleHidePane,
}: {
  hidePane: boolean;
  projects: Project[];
  toggleHidePane: React.Dispatch<React.SetStateAction<boolean>>;
}) {
  const { activeProject, activeProjectDispatch, flights } = useMapContext();

  if (hidePane) {
    return (
      <div className="z-1000 flex flex-col text-slate-700">
        <div className="flex p-2.5 items-center justify-between text-black">
          <button type="button">
            <Bars3Icon
              className="h-6 w-6 cursor-pointer"
              onClick={() => toggleHidePane(!hidePane)}
            />
          </button>
        </div>
      </div>
    );
  } else {
    return (
      <div className="z-1000 flex flex-col text-slate-700">
        <div className="flex p-2.5 items-center justify-between text-black">
          {activeProject ? (
            <button
              type="button"
              onClick={() => activeProjectDispatch({ type: 'clear', payload: null })}
            >
              <ArrowUturnLeftIcon className="h-6 w-6 cursor-pointer" />
            </button>
          ) : (
            <span></span>
          )}
          <XMarkIcon
            className="h-6 w-6 cursor-pointer float-right"
            onClick={() => toggleHidePane(!hidePane)}
          />
        </div>
        {activeProject ? (
          <article className="h-full border p-4">
            <h1>{activeProject.title}</h1>
            <HintText>{activeProject.description}</HintText>
            <ul className="mt-4 space-y-2 h-[calc(100vh_-_244px)] overflow-y-auto">
              {flights
                .sort((a, b) =>
                  new Date(a.acquisition_date) < new Date(b.acquisition_date) ? 1 : -1
                )
                .map((flight) => (
                  <li key={flight.id}>
                    <LayerCard>
                      <div>
                        <div className="flex items-center gap-4">
                          <MapIcon className="h-16 w-16" />
                          <div className="flex flex-col gap-2">
                            <strong className="font-bold text-slate-700">
                              {formatDate(flight.acquisition_date)}
                            </strong>
                            <div className="text-slate-600 text-sm">
                              <div>{flight.sensor} sensor</div>
                              <div className="flex gap-4">
                                <div>Altitude: {flight.altitude}m</div>
                                <div>
                                  Forward/side overlap: {flight.forward_overlap}%/
                                  {flight.side_overlap}%
                                </div>
                              </div>
                            </div>
                          </div>
                          <span className="inline-flex items-center justify-center rounded-full text-sky-700 bg-sky-100 px-2.5 py-0.5">
                            <PhotoIcon className="h-4 w-4 -ms-1 me-1.5" />
                            <p className="whitespace-nowrap text-sm">
                              {flight.data_products.length} Data Products
                            </p>
                          </span>
                        </div>
                        {flight.data_products.length > 0 ? (
                          <details className="group space-y-2 [&_summary::-webkit-details-marker]:hidden text-slate-600 overflow-visible">
                            {flight.data_products.map((data_product) => (
                              <LayerCard
                                key={data_product.id}
                                hover={true}
                                dataProduct={data_product}
                              >
                                <div className="text-slate-600 text-sm">
                                  <strong className="text-bold">
                                    {data_product.data_type}
                                  </strong>
                                  <div>Filename: {data_product.original_filename}</div>
                                  <div className="flex gap-4">
                                    <div>
                                      Bands:{' '}
                                      {data_product.band_info.bands.length > 1
                                        ? `Multi (${data_product.band_info.bands.length})`
                                        : 'Single'}
                                    </div>
                                    {data_product.band_info.bands.length === 1 ? (
                                      <>
                                        <div>
                                          Mean:{' '}
                                          {data_product.band_info.bands[0].stats.mean}
                                        </div>
                                        <div>
                                          Min:{' '}
                                          {
                                            data_product.band_info.bands[0].stats
                                              .minimum
                                          }
                                        </div>
                                        <div>
                                          Max:{' '}
                                          {
                                            data_product.band_info.bands[0].stats
                                              .maximum
                                          }
                                        </div>
                                      </>
                                    ) : null}
                                  </div>
                                </div>
                              </LayerCard>
                            ))}
                          </details>
                        ) : null}
                      </div>
                    </LayerCard>
                  </li>
                ))}
            </ul>
          </article>
        ) : (
          <article className="h-full border p-4 overflow-visible">
            <h1>Projects</h1>
            {projects.length > 0 ? (
              <ul className="mt-4 space-y-2 h-[calc(100vh_-_244px)] overflow-y-auto">
                {projects.map((project) => (
                  <li key={project.id}>
                    <LayerCard hover={true} project={project}>
                      <div>
                        <div className="flex items-center gap-4">
                          <MapPinIcon className="h-8 w-8" />
                          <div className="flex flex-col gap-2">
                            <strong className="font-bold text-slate-700">
                              {project.title}
                            </strong>
                            <div className="text-slate-600 text-sm">
                              <div>{project.description}</div>
                            </div>
                          </div>
                          <span className="inline-flex items-center justify-center rounded-full text-sky-700 bg-sky-100 px-2.5 py-0.5">
                            <PaperAirplaneIcon className="h-4 w-4 -ms-1 me-1.5" />
                            <p className="whitespace-nowrap text-sm">5 Flights</p>
                          </span>
                        </div>
                      </div>
                    </LayerCard>
                  </li>
                ))}
              </ul>
            ) : (
              <div>
                <p className="mb-4">
                  You do not currently have access to any projects. Use the below button
                  to create a new project.
                </p>
                <Link to="/projects/create">
                  <Button>Add first project</Button>
                </Link>
              </div>
            )}
          </article>
        )}
      </div>
    );
  }
}

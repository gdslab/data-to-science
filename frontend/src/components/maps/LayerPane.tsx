import { Link } from 'react-router-dom';
import {
  ArrowUturnLeftIcon,
  Bars3Icon,
  MapIcon,
  MapPinIcon,
  PaperAirplaneIcon,
  PhotoIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';

import { Button } from '../Buttons';
import HintText from '../HintText';
import { Project } from '../pages/projects/ProjectList';
import { useMapContext } from './MapContext';
import SymbologyControls from './SymbologyControls';
import { getDefaultSymbologySettings } from './MapContext';

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ');
}

function LayerCard({
  active = false,
  children,
  hover = false,
}: {
  active?: boolean;
  children: React.ReactNode;
  hover?: boolean;
}) {
  return (
    <div
      className={classNames(
        active ? 'border-accent1' : 'border-slate-200',
        hover && !active ? 'cursor-pointer hover:border-2 hover:border-accent1' : '',
        'p-2 rounded-sm shadow-sm bg-white border-solid border-2'
      )}
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
  const {
    activeDataProduct,
    activeDataProductDispatch,
    activeProject,
    activeProjectDispatch,
    flights,
    projectHoverStateDispatch,
    symbologySettingsDispatch,
  } = useMapContext();

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
                      <div className="grid grid-cols-4">
                        <div className="flex items-center justify-center">
                          <MapIcon className="h-16 w-16" />
                        </div>
                        <div className="col-span-2 flex flex-col items-start gap-2">
                          <strong className="font-bold text-slate-700">
                            {formatDate(flight.acquisition_date)}
                          </strong>
                          <div className="grid grid-rows-3 text-slate-700 text-sm gap-1.5">
                            <div>{flight.sensor} sensor</div>
                            <div>Altitude: {flight.altitude}m</div>
                            <div>
                              Forward/side overlap: {flight.forward_overlap}%/
                              {flight.side_overlap}%
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center justify-center">
                          <span className="inline-flex items-center justify-center rounded-full text-sky-700 bg-sky-100 px-2.5 py-0.5">
                            <PhotoIcon className="h-4 w-4 -ms-1 me-1.5" />
                            <p className="whitespace-nowrap text-sm">
                              {flight.data_products.length} Datasets
                            </p>
                          </span>
                        </div>
                      </div>
                      {flight.data_products.length > 0 ? (
                        <details
                          className="group space-y-2 [&_summary::-webkit-details-marker]:hidden text-slate-600 overflow-visible"
                          open={activeDataProduct ? true : false}
                        >
                          <summary className="text-sm">{`${flight.data_products.length} Data Products`}</summary>
                          {flight.data_products.map((dataProduct) => (
                            <LayerCard
                              key={dataProduct.id}
                              hover={true}
                              active={
                                activeDataProduct &&
                                dataProduct.id === activeDataProduct.id
                                  ? true
                                  : false
                              }
                            >
                              <div className="text-slate-600 text-sm">
                                <div
                                  className="grid grid-flow-row auto-rows-max"
                                  onClick={() => {
                                    if (
                                      (dataProduct && !activeDataProduct) ||
                                      (dataProduct &&
                                        activeDataProduct &&
                                        dataProduct.id !== activeDataProduct.id)
                                    ) {
                                      activeDataProductDispatch({
                                        type: 'set',
                                        payload: dataProduct,
                                      });
                                      if (dataProduct.user_style) {
                                        symbologySettingsDispatch({
                                          type: 'update',
                                          payload: dataProduct.user_style,
                                        });
                                      } else {
                                        symbologySettingsDispatch({
                                          type: 'update',
                                          payload:
                                            getDefaultSymbologySettings(dataProduct),
                                        });
                                      }
                                    }
                                  }}
                                >
                                  <strong className="text-bold">
                                    {dataProduct.data_type}
                                  </strong>
                                  <div>filename: {dataProduct.original_filename}</div>
                                  <div className="grid grid-flow-col auto-cols-max gap-1.5">
                                    bands:{' '}
                                    {dataProduct.stac_properties.eo.map((b) => {
                                      return (
                                        <span key={b.name} className="mr-2">
                                          {b.name} ({b.description})
                                        </span>
                                      );
                                    })}
                                  </div>
                                  <div className="grid grid-flow-col auto-cols-max gap-1.5">
                                    {dataProduct.stac_properties.raster.length === 1
                                      ? Object.keys(
                                          dataProduct.stac_properties.raster[0].stats
                                        ).map((k) => (
                                          <span key={k}>
                                            {k}
                                            {': '}
                                            {dataProduct.stac_properties.raster[0].stats[
                                              k
                                            ].toFixed(2)}
                                          </span>
                                        ))
                                      : null}
                                  </div>
                                </div>
                                {activeDataProduct &&
                                activeDataProduct.id === dataProduct.id ? (
                                  <div className="mt-2">
                                    <SymbologyControls
                                      dataProductType={dataProduct.data_type}
                                    />{' '}
                                  </div>
                                ) : null}
                              </div>
                            </LayerCard>
                          ))}
                        </details>
                      ) : null}
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
                    <LayerCard hover={true}>
                      <div
                        onClick={() => {
                          activeDataProductDispatch({ type: 'clear', payload: null });
                          activeProjectDispatch({ type: 'set', payload: project });
                        }}
                        onMouseOver={() => {
                          projectHoverStateDispatch({
                            type: 'set',
                            payload: project.id,
                          });
                        }}
                        onMouseLeave={() => {
                          projectHoverStateDispatch({ type: 'clear', payload: null });
                        }}
                      >
                        <div className="grid grid-cols-4">
                          <div className="flex items-center justify-center">
                            <MapPinIcon className="h-8 w-8" />
                          </div>
                          <div className="col-span-2 flex flex-col items-start gap-2">
                            <strong className="font-bold text-slate-700">
                              {project.title}
                            </strong>
                            <div className="text-slate-700 text-sm">
                              {project.description}
                            </div>
                          </div>
                          <div className="flex items-center justify-center">
                            <span className="inline-flex items-center justify-center rounded-full text-sky-700 bg-sky-100 px-2.5 py-0.5">
                              <PaperAirplaneIcon className="h-4 w-4 -ms-1 me-1.5" />
                              <p className="whitespace-nowrap text-sm">
                                {project.flight_count} Flights
                              </p>
                            </span>
                          </div>
                        </div>
                      </div>
                    </LayerCard>
                  </li>
                ))}
              </ul>
            ) : (
              <div>
                <p className="mb-4">
                  You do not have any projects to display on the map. Use the below
                  button to navigate to the Projects page and create your first project.
                </p>
                <Link to="/projects">
                  <Button>My Projects</Button>
                </Link>
              </div>
            )}
          </article>
        )}
      </div>
    );
  }
}

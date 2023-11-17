import { Link } from 'react-router-dom';
import {
  ArrowUturnLeftIcon,
  Bars3Icon,
  MapPinIcon,
  PaperAirplaneIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';

import { Button } from '../Buttons';
import { getDataProductName } from '../pages/projects/flights/dataProducts/DataProducts';
import HintText from '../HintText';
import { Project } from '../pages/projects/ProjectList';
import { useMapContext } from './MapContext';
import SymbologyControls from './SymbologyControls';
import { useEffect } from 'react';

import UASIcon from '../../assets/uas-icon.svg';
import { Band } from '../pages/projects/ProjectDetail';

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

function RasterStats({ stats }: { stats: Band['stats'] }) {
  return (
    <div className="grid grid-cols-4 gap-1.5">
      <span>Mean: {stats.mean.toFixed(2)}</span>
      <span>Min: {stats.minimum.toFixed(2)}</span>
      <span>Max: {stats.maximum.toFixed(2)}</span>
      <span>Std. Dev: {stats.stddev.toFixed(2)}</span>
    </div>
  );
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
  useEffect(() => {
    if (activeDataProduct && activeDataProduct.data_type === 'point_cloud')
      toggleHidePane(true);
  }, [activeDataProduct]);

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
                      <div className="grid grid-cols-6">
                        <div className="col-span-1 flex items-center justify-center">
                          <img src={UASIcon} width={'50%'} />
                        </div>
                        <div className="col-span-5 flex flex-col items-start gap-2">
                          <strong className="font-bold text-slate-700">
                            {formatDate(flight.acquisition_date)}
                          </strong>
                          <div className="grid grid-rows-2 text-slate-700 text-sm gap-1.5">
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <span className="text-sm text-slate-400 font-semibold">
                                  Platform:{' '}
                                </span>
                                {flight.platform.replace('_', ' ')}
                              </div>
                              <div>
                                <span className="text-sm text-slate-400 font-semibold">
                                  Sensor:
                                </span>{' '}
                                {flight.sensor}
                              </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <span className="text-sm text-slate-400 font-semibold">
                                  Altitude (m):
                                </span>{' '}
                                {flight.altitude}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                      {flight.data_products.length > 0 ? (
                        <details
                          className="group space-y-2 [&_summary::-webkit-details-marker]:hidden text-slate-600 overflow-visible"
                          open={activeDataProduct ? true : false}
                        >
                          <summary className="text-sm cursor-pointer">{`${flight.data_products.length} Data Products`}</summary>
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
                                      symbologySettingsDispatch({
                                        type: 'update',
                                        payload: dataProduct.user_style,
                                      });
                                    }
                                  }}
                                >
                                  <strong className="text-bold">
                                    {getDataProductName(dataProduct.data_type)}
                                  </strong>
                                  {dataProduct.data_type !== 'point_cloud' ? (
                                    <div className="grid grid-flow-col auto-cols-max gap-1.5">
                                      Bands:{' '}
                                      {dataProduct.stac_properties.eo.map((b) => {
                                        return (
                                          <span key={b.name} className="mr-2">
                                            {b.name} ({b.description})
                                          </span>
                                        );
                                      })}
                                    </div>
                                  ) : null}
                                  {dataProduct.data_type !== 'point_cloud' ? (
                                    <div className="grid grid-flow-col auto-cols-max gap-1.5">
                                      {dataProduct.stac_properties.raster.length ===
                                      1 ? (
                                        <RasterStats
                                          stats={
                                            dataProduct.stac_properties.raster[0].stats
                                          }
                                        />
                                      ) : null}
                                    </div>
                                  ) : null}
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

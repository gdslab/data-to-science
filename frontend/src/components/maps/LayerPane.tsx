import axios from 'axios';
import { useEffect } from 'react';
import { Link, SetURLSearchParams, useSearchParams } from 'react-router-dom';
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
import { DataProduct } from '../pages/projects/ProjectDetail';
import HintText from '../HintText';
import { Project } from '../pages/projects/ProjectList';
import SymbologyControl from './SymbologyControl';
import { useMapContext } from './MapContext';

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ');
}

function LayerCard({
  active = false,
  children,
  dataProduct = undefined,
  hover = false,
  project = undefined,
  setSearchParams = undefined,
}: {
  active?: boolean;
  children: React.ReactNode;
  dataProduct?: DataProduct;
  hover?: boolean;
  project?: Project;
  setSearchParams?: SetURLSearchParams;
}) {
  const {
    activeDataProduct,
    activeProjectDispatch,
    activeDataProductDispatch,
    geoRasterIdDispatch,
    projectHoverStateDispatch,
  } = useMapContext();

  return (
    <div
      className={classNames(
        active ? 'border-accent1' : 'border-slate-200',
        hover ? 'cursor-pointer hover:border-2 hover:border-accent1' : '',
        'p-2 rounded-sm shadow-sm bg-white border-solid border-2'
      )}
      onClick={() => {
        if (project) {
          if (setSearchParams) setSearchParams({});
          activeDataProductDispatch({ type: 'clear', payload: null });
          activeProjectDispatch({ type: 'set', payload: project });
        }
        if (
          (dataProduct && !activeDataProduct) ||
          (dataProduct && activeDataProduct && dataProduct.id !== activeDataProduct.id)
        ) {
          if (setSearchParams) setSearchParams({});
          activeDataProductDispatch({ type: 'set', payload: dataProduct });
          geoRasterIdDispatch({ type: 'create' });
        }
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
  const [searchParams, setSearchParams] = useSearchParams();
  const {
    activeDataProduct,
    activeProject,
    activeProjectDispatch,
    activeDataProductDispatch,
    flights,
  } = useMapContext();

  useEffect(() => {
    async function fetchDataProduct(
      projectId: string,
      flightId: string,
      dataProductId: string
    ) {
      try {
        const response = await axios.get(
          `/api/v1/projects/${projectId}/flights/${flightId}/data_products/${dataProductId}`
        );
        if (response) {
          const project = projects.filter(({ id }) => id === projectId);
          if (project) {
            activeProjectDispatch({ type: 'set', payload: project[0] });
            activeDataProductDispatch({ type: 'set', payload: response.data });
          } else {
            alert(
              'Requested resource does not exist or you do not have permission to view it'
            );
          }
        }
      } catch (err) {
        alert(
          'Requested resource does not exist or you do not have permission to view it'
        );
      }
    }

    const projectId = searchParams.get('projectId');
    const flightId = searchParams.get('flightId');
    const dataProductId = searchParams.get('dataProductId');

    if (projectId && flightId && dataProductId) {
      fetchDataProduct(projectId, flightId, dataProductId);
    }
  }, []);

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
                          {flight.data_products.map((data_product) => (
                            <LayerCard
                              key={data_product.id}
                              hover={true}
                              dataProduct={data_product}
                              active={
                                activeDataProduct &&
                                data_product.id === activeDataProduct.id
                                  ? true
                                  : false
                              }
                              setSearchParams={setSearchParams}
                            >
                              <div className="grid grid-flow-row auto-rows-max text-slate-600 text-sm">
                                <strong className="text-bold">
                                  {data_product.data_type}
                                </strong>
                                <div>filename: {data_product.original_filename}</div>
                                <div className="grid grid-flow-col auto-cols-max gap-1.5">
                                  bands:{' '}
                                  {data_product.stac_properties.eo.map((b) => {
                                    return (
                                      <span key={b.name} className="mr-2">
                                        {b.name} ({b.description})
                                      </span>
                                    );
                                  })}
                                </div>
                                <div className="grid grid-flow-col auto-cols-max gap-1.5">
                                  {data_product.stac_properties.raster.length === 1
                                    ? Object.keys(
                                        data_product.stac_properties.raster[0].stats
                                      ).map((k) => (
                                        <span key={k}>
                                          {k}
                                          {': '}
                                          {data_product.stac_properties.raster[0].stats[
                                            k
                                          ].toFixed(2)}
                                        </span>
                                      ))
                                    : null}
                                </div>
                                {activeDataProduct &&
                                activeDataProduct.id === data_product.id &&
                                data_product.data_type === 'dsm' ? (
                                  <div className="mt-2">
                                    <SymbologyControl />
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
                    <LayerCard hover={true} project={project}>
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

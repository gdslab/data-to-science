import './IForesterMap.css';
import L from 'leaflet';
import { useEffect, useRef, useState } from 'react';
import { MapContainer } from 'react-leaflet/MapContainer';
import { ZoomControl } from 'react-leaflet/ZoomControl';

import ClusterMarkers from './ClusterMarkers';
import IForesterControl from './IForesterControl';
import { useIForesterControlContext } from './IForesterContext';
import { useProjectContext } from '../ProjectContext';
import MapLayersControl from '../../../maps/MapLayersControl';
import { IForester } from '../Project';

export function getUniqueValues(array: (number | string)[]): (number | string)[] {
  return Array.from(new Set(array));
}

export default function IForesterMap() {
  const [filteredLocations, setFilteredLocations] = useState<IForester[]>([]);
  const { state, dispatch } = useIForesterControlContext();
  const { activeMarker, activeMarkerZoom, dbhMin, dbhMax, speciesSelection } = state;
  const { iforester } = useProjectContext();

  const mapRef = useRef<L.Map>(null);

  // set initial selected species
  useEffect(() => {
    if (iforester && iforester.length > 0 && speciesSelection.length === 0) {
      dispatch({
        type: 'SET_SPECIES_SELECTION',
        payload: getUniqueValues(
          iforester.map(({ species }) => species.toLowerCase())
        ) as string[],
      });
    }
  }, [iforester]);

  // set initial DBH min and DBH max
  useEffect(() => {
    if (iforester && iforester.length > 0) {
      if (dbhMin === -1) {
        dispatch({
          type: 'SET_DBH_MIN',
          payload: Math.min.apply(
            Math,
            iforester.map(({ dbh }) => dbh)
          ),
        });
      }
      if (dbhMax === -1) {
        dispatch({
          type: 'SET_DBH_MAX',
          payload: Math.max.apply(
            Math,
            iforester.map(({ dbh }) => dbh)
          ),
        });
      }
    }
  });

  // update locations when filter options change
  useEffect(() => {
    if (iforester && iforester.length > 0) {
      setFilteredLocations(
        iforester.filter(
          ({ dbh, species }) =>
            dbh >= dbhMin &&
            dbh <= dbhMax &&
            speciesSelection.includes(species.toLowerCase())
        )
      );
    }
  }, [dbhMin, dbhMax, iforester, speciesSelection]);

  useEffect(() => {
    if (mapRef.current && activeMarkerZoom) {
      const zoomMarker = filteredLocations.filter(({ id }) => id === activeMarkerZoom);
      if (zoomMarker.length > 0) {
        const coords = L.latLng([zoomMarker[0].latitude, zoomMarker[0].longitude]);
        mapRef.current.flyTo(coords, 18);
        dispatch({ type: 'SET_ACTIVE_MARKER_ZOOM', payload: '' });
      }
    }
  }, [activeMarkerZoom]);

  function updateVisibleMarkers(markers) {
    dispatch({
      type: 'SET_VISIBLE_MARKERS',
      payload: markers,
    });
  }

  return (
    <MapContainer
      ref={mapRef}
      center={[40.428655143949925, -86.9138040788386]}
      preferCanvas={true}
      zoom={8}
      maxZoom={24}
      scrollWheelZoom={true}
      zoomControl={false}
      worldCopyJump={true}
    >
      {iforester && (
        <ClusterMarkers
          activeMarker={activeMarker}
          markers={filteredLocations}
          updateVisibleMarkers={updateVisibleMarkers}
        />
      )}
      <IForesterControl position="topright" />
      <MapLayersControl />
      <ZoomControl position="topleft" />
    </MapContainer>
  );
}

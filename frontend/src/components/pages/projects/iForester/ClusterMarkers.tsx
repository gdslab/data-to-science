import L from 'leaflet';
import { useEffect, useMemo, useRef } from 'react';
import { CircleMarker } from 'react-leaflet/CircleMarker';
import { FeatureGroup } from 'react-leaflet/FeatureGroup';
import { useMapEvents } from 'react-leaflet/hooks';
import { useMap } from 'react-leaflet/hooks';
import MarkerClusterGroup from 'react-leaflet-cluster';
import { useIForesterControlContext } from './IForesterContext';

type Location = {
  id: string;
  latitude: number;
  longitude: number;
};

/**
 * Creates custom icon for marker cluster scaled by cluster child count.
 * @param {L.MarkerCluster} cluster Cluster created by markercluster.
 * @returns {L.DivIcon} Scaled custom icon.
 */
const createClusterCustomIcon = (cluster): L.DivIcon => {
  // scale factor for fonts and icons
  const scaleFactor = 4;

  // base size and max size for font
  const fontBaseSize = 16;
  const maxFontBaseSize = 64;
  // set fontSize to scaled or max value
  let fontSize = fontBaseSize + (scaleFactor / 2) * cluster.getChildCount();
  fontSize = fontSize < maxFontBaseSize ? fontSize : maxFontBaseSize;

  // base size and max size for icon
  const iconBaseSize = 30;
  const maxIconBaseSize = 120;
  // set iconSize to scaled or max value
  let iconSize = iconBaseSize + scaleFactor * cluster.getChildCount();
  iconSize = iconSize < maxIconBaseSize ? iconSize : maxIconBaseSize;

  // return scaled cluster icon
  return L.divIcon({
    html: `<span style="color: white; font-weight: 600; font-size: ${fontSize}px">${cluster.getChildCount()}</span>`,
    className:
      'flex items-center justify-center h-16 w-16 bg-[#3471ff]/90 border-2 border-[#3471ff] rounded-full',
    iconSize: L.point(iconSize, iconSize, true),
  });
};

export default function ClusterMarkers({
  activeMarker,
  markers,
  updateVisibleMarkers,
}: {
  activeMarker: string;
  markers: Location[];
  updateVisibleMarkers: (markers: string[]) => void;
}) {
  const { dispatch } = useIForesterControlContext();

  const map = useMap();

  const fgRef = useRef<L.FeatureGroup>(null);

  const _updateVisibleMarkers = () => {
    let visibleMarkers: string[] = [];
    if (markers.length > 0) {
      markers.forEach((marker) => {
        const coords = L.latLng([marker.latitude, marker.longitude]);
        if (map.getBounds().contains(coords)) {
          visibleMarkers.push(marker.id);
        }
      });
      updateVisibleMarkers(visibleMarkers);
    }
  };

  // zoom to extent of markers
  useEffect(() => {
    if (fgRef.current) {
      map.fitBounds(fgRef.current.getBounds(), { maxZoom: 16 });
      _updateVisibleMarkers();
    }
  }, [markers]);

  // update which markers are visible on the map after the map moves
  useMapEvents({
    moveend(_e) {
      _updateVisibleMarkers();
    },
  });

  // event handler for interactions with map markers
  const eventHandlers = useMemo(
    () => ({
      mouseover(e) {
        const markerId = e.sourceTarget.options.markerId;
        if (markerId) dispatch({ type: 'SET_ACTIVE_MARKER', payload: markerId });
      },
      mouseout(e) {
        const markerId = e.sourceTarget.options.markerId;
        if (markerId) dispatch({ type: 'SET_ACTIVE_MARKER', payload: '' });
      },
    }),
    []
  );

  if (markers.length === 0) return null;

  return (
    <FeatureGroup ref={fgRef}>
      <MarkerClusterGroup
        iconCreateFunction={createClusterCustomIcon}
        showCoverageOnHover={false}
      >
        {markers.map(({ id, latitude, longitude }) => (
          <CircleMarker
            key={id}
            // @ts-ignore
            markerId={id}
            center={[latitude, longitude]}
            radius={10}
            pathOptions={{
              color: 'black',
              fillColor: id === activeMarker ? '#3471FF' : 'white',
              fillOpacity: 1,
              stroke: true,
            }}
            eventHandlers={eventHandlers}
          />
        ))}
      </MarkerClusterGroup>
    </FeatureGroup>
  );
}

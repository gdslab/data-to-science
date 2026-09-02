import { Tab, TabGroup, TabList, TabPanel, TabPanels } from '@headlessui/react';
import { Feature } from 'geojson';
import type { PositionAnchor } from 'maplibre-gl';
import { ReactNode, useMemo, useState } from 'react';
import { MapRef, Popup, useMap } from 'react-map-gl/maplibre';
import area from '@turf/area';

import FeaturePreviewImage from './FeaturePreviewImage';
import { PopupInfoProps } from './HomeMap';
import { useMapContext } from './MapContext';
import { useRasterSymbologyContext } from './RasterSymbologyContext';
import StripedTable from '../StripedTable';
import { useZonalStatistics } from './useZonalStatistics';
import { isSingleBand } from './utils';
import { ZonalStatisticsPanel } from './ZonalStatistics';

type FeaturePopupProps = {
  popupInfo: PopupInfoProps;
  onClose: () => void;
};

type PopupTabKey = 'attributes' | 'preview' | 'zonal';

type PopupTab = {
  key: PopupTabKey;
  label: string;
  content: ReactNode;
};

type PopupPlacement = {
  anchor: PositionAnchor;
  offset: [number, number];
  width: number;
  maxHeight: number;
};

const POPUP_MARGIN = 16;
const POPUP_MIN_WIDTH = 200;
const POPUP_MAX_WIDTH = 400;
const POPUP_MIN_HEIGHT = 220;
const POPUP_MAX_HEIGHT = 560;
const TIP_HEIGHT = 10;

const TAB_CLASS =
  '-mb-px border-b-2 border-transparent px-1 py-2 text-sm font-medium text-slate-500 whitespace-nowrap focus:outline-hidden focus-visible:ring-2 focus-visible:ring-primary data-hover:text-slate-800 data-selected:border-primary data-selected:text-primary';

/**
 * Picks the side of the click point with the most room and caps the popup
 * body height to that room, so the popup never extends past the map edge.
 */
function getPopupPlacement(
  map: MapRef | undefined,
  lng: number,
  lat: number
): PopupPlacement {
  if (!map) {
    return {
      anchor: 'top',
      offset: [0, 0],
      width: POPUP_MAX_WIDTH,
      maxHeight: POPUP_MAX_HEIGHT,
    };
  }

  const { x, y } = map.project([lng, lat]);
  const { clientWidth: mapW, clientHeight: mapH } = map.getContainer();
  const width = Math.max(
    POPUP_MIN_WIDTH,
    Math.min(POPUP_MAX_WIDTH, mapW - 2 * POPUP_MARGIN)
  );

  // A 'top' anchor hangs the popup below the point
  const above = y;
  const below = mapH - y;
  const vertical: 'top' | 'bottom' = below >= above ? 'top' : 'bottom';
  const room = vertical === 'top' ? below : above;
  const maxHeight = Math.max(
    POPUP_MIN_HEIGHT,
    Math.min(POPUP_MAX_HEIGHT, room - POPUP_MARGIN - TIP_HEIGHT)
  );

  let anchor: PositionAnchor = vertical;
  let dx = 0;
  const fitsCentered =
    x - width / 2 >= POPUP_MARGIN && x + width / 2 <= mapW - POPUP_MARGIN;
  if (!fitsCentered) {
    if (x + width <= mapW - POPUP_MARGIN) {
      anchor = `${vertical}-left`;
    } else if (x - width >= POPUP_MARGIN) {
      anchor = `${vertical}-right`;
    } else {
      dx = mapW / 2 - x;
    }
  }

  return { anchor, offset: [dx, 0], width, maxHeight };
}

function FeatureHeader({ feature }: { feature: Feature }) {
  const attrs = feature.properties;

  if (!attrs) {
    return <div>No title</div>;
  }

  return (
    <div className="flex flex-col">
      <span className="text-lg font-bold wrap-anywhere">{attrs.layer_name}</span>
      {feature.geometry.type === 'Polygon' ? (
        <span className="text-sm text-slate-600">
          Area: {area(feature).toFixed(2)} m&sup2;
        </span>
      ) : null}
    </div>
  );
}

function FeatureAttributes({ feature }: { feature: Feature }) {
  const attrs = feature.properties;

  if (!attrs) {
    return <span>No attributes</span>;
  }

  return (
    <div className="overflow-hidden rounded-lg border border-gray-200">
      <StripedTable
        wrap
        headers={['Name', 'Value']}
        values={Object.keys(attrs).map((key) => ({
          label: key,
          value: String(attrs[key] ?? ''),
        }))}
      />
    </div>
  );
}

export default function FeaturePopup({
  popupInfo,
  onClose,
}: FeaturePopupProps) {
  const { feature, longitude, latitude } = popupInfo;
  const { current: map } = useMap();
  const { activeDataProduct, activeProject } = useMapContext();
  const { state } = useRasterSymbologyContext();
  const [selectedKey, setSelectedKey] = useState<PopupTabKey>('attributes');

  const placement = useMemo(
    () => getPopupPlacement(map, longitude, latitude),
    [map, longitude, latitude]
  );

  const isPolygon =
    feature.geometry.type === 'Polygon' ||
    feature.geometry.type === 'MultiPolygon';
  const symbology = activeDataProduct
    ? (state[activeDataProduct.id]?.symbology ?? null)
    : null;
  const showZonal =
    !!activeDataProduct && isPolygon && isSingleBand(activeDataProduct);

  const zonal = useZonalStatistics({
    enabled: showZonal,
    dataProduct: activeDataProduct,
    projectId: activeProject?.id ?? null,
    feature,
  });

  const tabs: PopupTab[] = [
    {
      key: 'attributes',
      label: 'Attributes',
      content: <FeatureAttributes feature={feature} />,
    },
  ];
  if (activeDataProduct && symbology && isPolygon) {
    tabs.push({
      key: 'preview',
      label: 'Preview',
      content: (
        <FeaturePreviewImage
          dataProduct={activeDataProduct}
          feature={feature}
          symbology={symbology}
        />
      ),
    });
  }
  if (showZonal) {
    tabs.push({
      key: 'zonal',
      label: 'Zonal Stats',
      content: <ZonalStatisticsPanel {...zonal} />,
    });
  }

  // Derive the index from a key so selection survives tabs appearing/disappearing
  const selectedIndex = Math.max(
    0,
    tabs.findIndex((tab) => tab.key === selectedKey)
  );

  const isTabbed = tabs.length > 1;

  return (
    <Popup
      className="feature-popup"
      longitude={longitude}
      latitude={latitude}
      anchor={placement.anchor}
      offset={placement.offset}
      maxWidth={`${placement.width}px`}
      style={{ width: placement.width }}
      onClose={onClose}
    >
      <article
        className="flex flex-col overflow-hidden"
        style={{ maxHeight: placement.maxHeight }}
      >
        <header className="shrink-0 px-3 pt-3 pr-9">
          <FeatureHeader feature={feature} />
        </header>
        {isTabbed ? (
          <TabGroup
            selectedIndex={selectedIndex}
            onChange={(index) => setSelectedKey(tabs[index].key)}
            className="contents"
          >
            <TabList className="shrink-0 flex gap-4 px-3 mt-1 border-b border-slate-200">
              {tabs.map((tab) => (
                <Tab key={tab.key} className={TAB_CLASS}>
                  {tab.label}
                </Tab>
              ))}
            </TabList>
            {/* Fixed body height so switching tabs never resizes the popup;
                min-h-0 lets it shrink under the article's max height */}
            <TabPanels className="h-72 shrink min-h-0">
              {tabs.map((tab) => (
                <TabPanel
                  key={tab.key}
                  unmount={false}
                  className="h-full overflow-y-auto p-3 focus:outline-hidden"
                >
                  {tab.content}
                </TabPanel>
              ))}
            </TabPanels>
          </TabGroup>
        ) : (
          <div className="flex-1 min-h-0 overflow-y-auto p-3">
            {tabs[0].content}
          </div>
        )}
      </article>
    </Popup>
  );
}

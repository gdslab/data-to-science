import { LayersControl, WMSTileLayer } from 'react-leaflet';

export default function MapLayersControl() {
  return (
    <LayersControl position="topright">
      {/* Basemaps */}
      <LayersControl.BaseLayer name="USGS Topo" checked>
        <WMSTileLayer
          url="https://basemap.nationalmap.gov/arcgis/services/USGSTopo/MapServer/WMSServer"
          layers="0"
          format="image/png"
          transparent={true}
          // attribution="USGS The National Map: National Boundaries Dataset, 3DEP Elevation Program, Geographic Names Information System, National Hydrography Dataset, National Land Cover Database, National Structures Dataset, and National Transportation Dataset; USGS Global Ecosystems; U.S. Census Bureau TIGER/Line data; USFS Road Data; Natural Earth Data; U.S. Department of State Humanitarian Information Unit; and NOAA National Centers for Environmental Information, U.S. Coastal Relief Model. Data refreshed June, 2022."
        />
      </LayersControl.BaseLayer>
      <LayersControl.BaseLayer name="USGS ImageryTopo">
        <WMSTileLayer
          url="https://basemap.nationalmap.gov/arcgis/services/USGSImageryTopo/MapServer/WMSServer"
          layers="0"
          format="image/png"
          transparent={true}
          // attribution="USGS The National Map: Orthoimagery and US Topo. Data refreshed January, 2022."
        />
      </LayersControl.BaseLayer>
    </LayersControl>
  );
}

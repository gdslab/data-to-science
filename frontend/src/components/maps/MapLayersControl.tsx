import { LayersControl, TileLayer, WMSTileLayer } from 'react-leaflet';

export default function MapLayersControl() {
  return (
    <LayersControl position="topright">
      {/* Basemaps */}
      <LayersControl.BaseLayer name="OpenStreetMap" checked>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
      </LayersControl.BaseLayer>
      <LayersControl.BaseLayer name="USGS Topo">
        <WMSTileLayer
          attribution="USGS The National Map: National Boundaries Dataset, 3DEP Elevation Program, Geographic Names Information System, National Hydrography Dataset, National Land Cover Database, National Structures Dataset, and National Transportation Dataset; USGS Global Ecosystems; U.S. Census Bureau TIGER/Line data; USFS Road Data; Natural Earth Data; U.S. Department of State Humanitarian Information Unit; and NOAA National Centers for Environmental Information, U.S. Coastal Relief Model. Data refreshed June, 2022."
          format="image/png"
          layers="0"
          transparent={true}
          url="https://basemap.nationalmap.gov/arcgis/services/USGSTopo/MapServer/WMSServer"
        />
      </LayersControl.BaseLayer>
      <LayersControl.BaseLayer name="USGS ImageryTopo">
        <WMSTileLayer
          attribution="USGS The National Map: Orthoimagery and US Topo. Data refreshed January, 2022."
          format="image/png"
          layers="0"
          transparent={true}
          url="https://basemap.nationalmap.gov/arcgis/services/USGSImageryTopo/MapServer/WMSServer"
        />
      </LayersControl.BaseLayer>
    </LayersControl>
  );
}

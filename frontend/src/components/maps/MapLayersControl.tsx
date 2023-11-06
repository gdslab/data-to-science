import { LayersControl, TileLayer, WMSTileLayer } from 'react-leaflet';

export default function MapLayersControl() {
  return (
    <LayersControl position="topright">
      {/* Basemaps */}
      <LayersControl.BaseLayer name="OpenStreetMap">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          maxNativeZoom={18}
          maxZoom={24}
        />
      </LayersControl.BaseLayer>
      <LayersControl.BaseLayer name="USGS Topo">
        <WMSTileLayer
          attribution="USGS The National Map: National Boundaries Dataset, 3DEP Elevation Program, Geographic Names Information System, National Hydrography Dataset, National Land Cover Database, National Structures Dataset, and National Transportation Dataset; USGS Global Ecosystems; U.S. Census Bureau TIGER/Line data; USFS Road Data; Natural Earth Data; U.S. Department of State Humanitarian Information Unit; and NOAA National Centers for Environmental Information, U.S. Coastal Relief Model. Data refreshed April, 2023."
          url="https://basemap.nationalmap.gov/arcgis/services/USGSTopo/MapServer/WMSServer"
          format="image/png"
          layers="0"
          transparent={true}
          maxNativeZoom={16}
          maxZoom={24}
        />
      </LayersControl.BaseLayer>
      <LayersControl.BaseLayer name="USGS Imagery" checked>
        <WMSTileLayer
          attribution="USGS The National Map: Orthoimagery. Data refreshed December, 2021."
          url="https://basemap.nationalmap.gov/arcgis/services/USGSImageryOnly/MapServer/WMSServer"
          format="image/png"
          layers="0"
          transparent={true}
          maxNativeZoom={16}
          maxZoom={24}
        />
      </LayersControl.BaseLayer>
      <LayersControl.BaseLayer name="USGS ImageryTopo">
        <WMSTileLayer
          attribution="USGS The National Map: Orthoimagery and US Topo. Data refreshed August, 2023."
          url="https://basemap.nationalmap.gov/arcgis/services/USGSImageryTopo/MapServer/WMSServer"
          format="image/png"
          layers="0"
          transparent={true}
          maxNativeZoom={16}
          maxZoom={24}
        />
      </LayersControl.BaseLayer>
    </LayersControl>
  );
}

import * as L from 'leaflet';
import { useEffect } from 'react';
import { useMap } from 'react-leaflet/hooks';
import 'leaflet-measure';
import 'leaflet-measure/dist/leaflet-measure.css';

// extend leaflet control with Measure
declare module 'leaflet' {
  namespace Control {
    function measure(options?: any): Control.Measure;
    class Measure extends Control {
      constructor(options?: any);
    }
  }

  function control(options?: any): any;
  namespace control {
    function measure(options?: any): Control.Measure;
  }
}

export default function LeafletMeasureControl() {
  const map = useMap();

  useEffect(() => {
    // https://github.com/ljagis/leaflet-measure/issues/171#issuecomment-1137483548
    L.Control.Measure.include({
      // set icon on the capture marker
      _setCaptureMarkerIcon: function () {
        // disable autopan
        this._captureMarker.options.autoPanOnFocus = false;

        // default function
        this._captureMarker.setIcon(
          L.divIcon({
            iconSize: this._map.getSize().multiplyBy(2),
          })
        );
      },
    });
    const measureControl = L.control
      .measure({
        position: 'topleft',
        activeColor: '#f4d03f',
        completedColor: '#f9e79f',
      })
      .addTo(map);

    return () => {
      measureControl.remove();
    };
  }, []);

  return null;
}

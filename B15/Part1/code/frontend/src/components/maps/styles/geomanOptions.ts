import { GmOptionsPartial } from '@geoman-io/maplibre-geoman-free';

export const geomanOptions: GmOptionsPartial = {
  controls: {
    helper: {
      shape_markers: {
        uiEnabled: false,
      },
      snapping: {
        uiEnabled: false,
        active: true,
      },
      zoom_to_features: {
        uiEnabled: false,
      },
    },
    draw: {
      marker: {
        uiEnabled: false,
      },
      circle: {
        uiEnabled: false,
      },
      circle_marker: {
        uiEnabled: false,
      },
      text_marker: {
        uiEnabled: false,
      },
      line: {
        uiEnabled: false,
      },
      rectangle: {
        uiEnabled: false,
      },
      polygon: {
        title: 'Draw Polygon',
        uiEnabled: true,
        active: false,
      },
    },
    edit: {
      drag: {
        uiEnabled: false,
      },
      change: {
        title: 'Edit Polygon',
        uiEnabled: true,
      },
      rotate: {
        uiEnabled: false,
      },
      scale: {
        uiEnabled: false,
      },
      copy: {
        uiEnabled: false,
      },
      cut: {
        uiEnabled: false,
      },
    },
  },
  layerStyles: {
    polygon: {
      // Style for the main layer
      gm_main: [
        {
          type: 'fill',
          paint: {
            'fill-color': '#1E90FF',
            'fill-opacity': 0.35,
            'fill-outline-color': '#F5F5F5',
          },
        },
        {
          type: 'line',
          paint: {
            'line-color': '#F5F5F5',
            'line-width': 3,
            'line-opacity': 1.0,
          },
        },
      ],
    },
    line: {
      // Style for the temporary layer while drawing
      gm_temporary: [
        {
          type: 'line',
          paint: {
            'line-color': '#F5F5F5',
            'line-width': 4,
            'line-opacity': 1.0,
            'line-dasharray': [2, 2],
          },
        },
      ],
    },
  },
};

// You can also export individual option configurations if needed
export const geomanSnappingOptions = {
  uiEnabled: true,
  active: true,
};

export const geomanControlOptions = {
  helper: {
    snapping: geomanSnappingOptions,
  },
};

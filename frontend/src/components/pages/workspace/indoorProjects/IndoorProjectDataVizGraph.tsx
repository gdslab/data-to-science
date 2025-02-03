import { useMemo } from 'react';

import {
  IndoorProjectDataVizAPIResponse,
  IndoorProjectDataVizRecord,
} from './IndoorProject';

function hsiToHex(H, S, I) {
  H = H % 360; // Ensure hue is within 0-360
  S = Math.max(0, Math.min(1, S)); // Clamp S to [0, 1]
  I = Math.max(0, Math.min(1, I)); // Clamp I to [0, 1]

  let R, G, B;

  if (H < 120) {
    R =
      I *
      (1 +
        (S * Math.cos((H * Math.PI) / 180)) /
          Math.cos(((60 - H) * Math.PI) / 180));
    B = I * (1 - S);
    G = 3 * I - (R + B);
  } else if (H < 240) {
    H -= 120;
    G =
      I *
      (1 +
        (S * Math.cos((H * Math.PI) / 180)) /
          Math.cos(((60 - H) * Math.PI) / 180));
    R = I * (1 - S);
    B = 3 * I - (R + G);
  } else {
    H -= 240;
    B =
      I *
      (1 +
        (S * Math.cos((H * Math.PI) / 180)) /
          Math.cos(((60 - H) * Math.PI) / 180));
    G = I * (1 - S);
    R = 3 * I - (G + B);
  }

  // Convert to 8-bit [0, 255] range and ensure valid values
  R = Math.max(0, Math.min(255, Math.round(R * 255)));
  G = Math.max(0, Math.min(255, Math.round(G * 255)));
  B = Math.max(0, Math.min(255, Math.round(B * 255)));

  // Convert RGB to Hex
  return `#${((1 << 24) | (R << 16) | (G << 8) | B)
    .toString(16)
    .slice(1)
    .toUpperCase()}`;
}

const getTextColor = (h, s, l) => {
  if (!h || !s || !l) return 'text-black';

  // Convert HSL (0-360, 0-100, 0-100) to RGB
  s /= 100;
  l /= 100;

  const C = (1 - Math.abs(2 * l - 1)) * s;
  const X = C * (1 - Math.abs(((h / 60) % 2) - 1));
  const m = l - C / 2;

  let r, g, b;
  if (h < 60) [r, g, b] = [C, X, 0];
  else if (h < 120) [r, g, b] = [X, C, 0];
  else if (h < 180) [r, g, b] = [0, C, X];
  else if (h < 240) [r, g, b] = [0, X, C];
  else if (h < 300) [r, g, b] = [X, 0, C];
  else [r, g, b] = [C, 0, X];

  // Convert RGB from [0,1] to [0,255]
  r = Math.round((r + m) * 255);
  g = Math.round((g + m) * 255);
  b = Math.round((b + m) * 255);

  // Calculate luminance (per WCAG)
  const luminance =
    0.2126 * (r / 255) + 0.7152 * (g / 255) + 0.0722 * (b / 255);

  // Return Tailwind class based on luminance
  return luminance > 0.5 ? 'text-black' : 'text-white';
};

export default function IndoorProjectDataVizGraph({
  data,
}: {
  data: IndoorProjectDataVizAPIResponse;
}) {
  const result: IndoorProjectDataVizRecord[][] = useMemo(() => {
    const groupedData = data.results.reduce((acc, item) => {
      const { treatment } = item;
      if (!acc[treatment]) {
        acc[treatment] = [];
      }
      acc[treatment].push(item);
      return acc;
    }, {});

    return Object.values(groupedData);
  }, []);

  return (
    <div className="flex flex-col gap-8">
      {result.map((group, i) => (
        <div>
          <span className="text-lg font-bold">{`Group ${i + 1}`}</span>
          <div key={i} className="flex gap-2">
            {group
              .sort((a, b) => a.interval_days - b.interval_days)
              .map((record, j) => (
                <div
                  key={j}
                  className={`w-60 p-2.5 flex flex-col border-2 border-gray-300 shadow-md ${getTextColor(
                    record.hue,
                    record.saturation,
                    record.intensity
                  )}`}
                  style={{
                    backgroundColor:
                      record.hue && record.saturation && record.intensity
                        ? `hsl(${record.hue}, ${record.saturation}%, ${record.intensity}%)`
                        : '#fff',
                  }}
                >
                  <div className="font-semibold">{record.treatment}</div>
                  <div className="flex justify-between gap-4">
                    <span>Hue:</span>
                    <span>{record.hue?.toFixed(2) || 'NA'}</span>
                  </div>
                  <div className="flex justify-between gap-4">
                    <span>Saturation:</span>
                    <span>{record.saturation?.toFixed(2) || 'NA'}</span>
                  </div>
                  <div className="flex justify-between gap-4">
                    <span>Intensity:</span>
                    <span>{record.intensity?.toFixed(2) || 'NA'}</span>
                  </div>
                </div>
              ))}
          </div>
        </div>
      ))}
      <div className="flex gap-2">
        {result?.[0].map((record) => (
          <div
            key={`interval-${record.interval_days}`}
            className="w-60 p-2.5 text-center text-lg font-bold"
          >
            {record.interval_days}
          </div>
        ))}
      </div>
      <div className="w-full text-center font-semibold">Day Intervals</div>
    </div>
  );
}

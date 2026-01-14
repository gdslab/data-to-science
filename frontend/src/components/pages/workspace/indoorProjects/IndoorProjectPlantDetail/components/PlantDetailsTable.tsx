import { PlantDetailAndChart } from '../types';
import React from 'react';

const HeaderCell = ({ children }: { children: React.ReactNode }) => (
  <th className="p-2">{children}</th>
);

const Cell = ({ children }: { children: React.ReactNode }) => (
  <td className={`mx-1 my-2 p-2 bg-white`}>{children}</td>
);

export default function PlantDetailsTable({
  data,
}: {
  data: PlantDetailAndChart;
}) {
  const indoorProjectPlant = data;
  return (
    <table className="min-w-[600px] w-full border-separate border-spacing-y-1 border-spacing-x-1">
      <thead>
        <tr className="h-12 sticky top-0 text-slate-700 bg-slate-300">
          {Object.keys(indoorProjectPlant.ppew).map((key) => (
            <HeaderCell key={key}>{key}</HeaderCell>
          ))}
        </tr>
      </thead>
      <tbody>
        <tr>
          {Object.keys(indoorProjectPlant.ppew).map((key) => (
            <Cell key={key}>
              <span title={indoorProjectPlant.ppew[key]}>
                {indoorProjectPlant.ppew[key]}
              </span>
            </Cell>
          ))}
        </tr>
      </tbody>
    </table>
  );
}

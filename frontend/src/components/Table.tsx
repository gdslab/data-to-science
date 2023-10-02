import { Link } from 'react-router-dom';
import { ReactNode } from 'react';

interface Action {
  key: string;
  color: string;
  icon: ReactNode;
  label: string;
  url: string;
}

export function TableBody({
  actions,
  rows,
}: {
  actions?: Action[][];
  rows: (string | JSX.Element)[][];
}) {
  return (
    <tbody className="divide-y divide-gray-200 bg-white">
      {rows.map((row, i) => (
        <tr key={`row-${i}`}>
          {row.map((value, j) => (
            <td key={`cell-${i},${j}`} className="p-4 text-slate-500 text-center">
              {value}
            </td>
          ))}
          {actions ? (
            <td className="p-4 text-slate-500">
              <div className="flex justify-around">
                {actions[i].map((action) => (
                  <Link
                    key={action.key}
                    className={`text-${action.color}-600`}
                    to={action.url}
                  >
                    <div className="flex items-center">
                      <div className="relative rounded-full accent3 p-1 focus:outline-none">
                        {action.icon ? action.icon : null}
                      </div>
                      <span>{action.label}</span>
                    </div>
                  </Link>
                ))}
              </div>
            </td>
          ) : null}
        </tr>
      ))}
    </tbody>
  );
}

export function TableHead({ columns }: { columns: string[] }) {
  return (
    <thead className="bg-slate-200">
      <tr>
        {columns.map((col) => (
          <th
            key={col.replace(/\s+/g, '').toLowerCase()}
            className="font-semibold p-4 text-md text-slate-600 text-center"
          >
            {col}
          </th>
        ))}
      </tr>
    </thead>
  );
}

export default function Table({ children }: { children: React.ReactNode }) {
  return (
    <table className="table-auto border-separate border-spacing-1 w-full">
      {children}
    </table>
  );
}

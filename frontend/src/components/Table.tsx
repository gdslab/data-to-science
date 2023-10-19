import { ReactNode } from 'react';
import { Link } from 'react-router-dom';

import { classNames } from './utils';

interface Action {
  component?: React.ReactNode | null;
  key: string;
  icon: ReactNode;
  label: string;
  onClick?: () => void;
  type?: string;
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
            <td key={`cell-${i},${j}`} className="p-4">
              <div className="flex grow-0 items-center justify-center">{value}</div>
            </td>
          ))}
          {actions ? (
            <td className="p-4 text-slate-500">
              <div className="flex justify-around">
                {actions[i].map((action) =>
                  action.type === 'button' ? (
                    <div key={action.key}>
                      <button
                        className={classNames(
                          action.label === 'Delete' ? 'text-red-600' : 'text-sky-600',
                          'flex items-center cursor-pointer text-sm'
                        )}
                        onClick={(e) => {
                          e.preventDefault();
                          if (action.onClick) {
                            action.onClick();
                          }
                        }}
                      >
                        <div className="relative rounded-full accent3 p-1 focus:outline-none">
                          {action.icon ? action.icon : null}
                        </div>
                        <span>{action.label}</span>
                      </button>
                      {action.component ? action.component : null}
                    </div>
                  ) : (
                    <Link
                      key={action.key}
                      className={classNames(
                        action.label === 'Delete' ? 'text-red-600' : 'text-sky-600',
                        'text-sm'
                      )}
                      to={action.url}
                    >
                      <div className="flex items-center">
                        <div className="relative rounded-full accent3 p-1 focus:outline-none">
                          {action.icon ? action.icon : null}
                        </div>
                        <span>{action.label}</span>
                      </div>
                    </Link>
                  )
                )}
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

import { ReactNode } from 'react';
import { Link } from 'react-router-dom';

import { classNames } from './utils';

interface Action {
  key: string;
  icon: ReactNode;
  label: string;
  onClick?: () => void;
  type?: string;
  url: string;
}

function TableRow({ children }: { children: ReactNode }) {
  return <div className="flex flex-wrap gap-1.5 mb-1.5">{children}</div>;
}

function TableCell({ children }: { children: ReactNode }) {
  return (
    <div className="flex-1 flex p-4 items-center justify-center text-center bg-white">
      {children}
    </div>
  );
}

export function TableBody({
  actions,
  rows,
}: {
  actions?: Action[][];
  rows: (string | JSX.Element)[][];
}) {
  return (
    <div className="overflow-y-scroll">
      {rows.map((row, i) => (
        <TableRow key={`row-${i}`}>
          {row.map((value, j) => (
            <TableCell key={`cell-${i},${j}`}>{value}</TableCell>
          ))}
          {actions ? (
            <TableCell>
              <div className="h-full flex items-center justify-around">
                {actions[i].map((action) =>
                  action.type === 'button' ? (
                    <div key={action.key}>
                      <button
                        className={classNames(
                          action.label === 'Delete'
                            ? '!text-red-600 visited:text-red-600'
                            : '!text-sky-600 visited:text-sky-600',
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
                    </div>
                  ) : (
                    <Link
                      key={action.key}
                      className={classNames(
                        action.label === 'Delete'
                          ? '!text-red-600 visited:text-red-600'
                          : '!text-sky-600 visited:!text-sky-600',
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
            </TableCell>
          ) : null}
        </TableRow>
      ))}
    </div>
  );
}

export function TableHead({ columns }: { columns: string[] }) {
  return (
    <TableRow>
      {columns.map((col) => (
        <div
          key={col.replace(/\s+/g, '').toLowerCase()}
          className="flex-1 p-4 text-center font-semibold text-md text-slate-600"
        >
          {col}
        </div>
      ))}
    </TableRow>
  );
}

export default function Table({
  children,
  height,
}: {
  children: React.ReactNode;
  height?: number;
}) {
  return (
    <div
      className={classNames(
        height ? `h-${height}` : '',
        'flex flex-col w-full overflow-y-auto border-separate border-spacing-1'
      )}
    >
      {children}
    </div>
  );
}

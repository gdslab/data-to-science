import { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { v4 as uuidv4 } from 'uuid';

import { classNames } from './utils';

export interface Action {
  key: string;
  component?: ReactNode;
  icon?: ReactNode;
  label: string;
  onClick?: () => void;
  type?: string;
  url?: string;
}

function TableRow({ children }: { children: ReactNode }) {
  return (
    <div key={uuidv4()} className="flex flex-wrap gap-1.5 mb-1.5">
      {children}
    </div>
  );
}

function TableCell({ align, children }: { align: string; children: ReactNode }) {
  return (
    <div
      className={classNames(
        align === 'left'
          ? 'justify-start text-left'
          : align === 'right'
          ? 'justify-end text-right'
          : 'justify-center text-center',
        'flex-1 flex p-4 items-center bg-white'
      )}
    >
      {children}
    </div>
  );
}

export function TableBody({
  actions,
  align = 'center',
  rows,
}: {
  actions?: Action[][];
  align?: string;
  rows: (string | JSX.Element)[][];
}) {
  return (
    <div className="overflow-y-scroll">
      {rows.map((row, i) => (
        <TableRow key={`row-${i}`}>
          {row.map((value, j) => (
            <TableCell align={align} key={`cell-${i},${j}`}>
              {value}
            </TableCell>
          ))}
          {actions ? (
            <TableCell align={align}>
              <div className="w-full h-full flex items-center justify-around">
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
                  ) : action.type === 'component' && action.component ? (
                    <div key={action.key}>{action.component}</div>
                  ) : (
                    <Link
                      key={action.key}
                      className={classNames(
                        action.label === 'Delete'
                          ? '!text-red-600 visited:text-red-600'
                          : '!text-sky-600 visited:!text-sky-600',
                        'text-sm'
                      )}
                      to={action.url ? action.url : ''}
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

export function TableHead({
  align = 'center',
  columns,
}: {
  align?: string;
  columns: string[];
}) {
  return (
    <TableRow>
      {columns.map((col) => (
        <div
          key={col.replace(/\s+/g, '').toLowerCase()}
          className={classNames(
            align === 'left'
              ? 'text-left'
              : align === 'right'
              ? 'text-right'
              : 'text-center',
            'flex-1 p-4 font-semibold text-md text-slate-600'
          )}
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

import { Link } from 'react-router-dom';

interface Action {
  key: string;
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
                    className={
                      action.key.split('-')[1] === 'edit'
                        ? 'text-sky-600'
                        : 'text-red-600'
                    }
                    to={action.url}
                  >
                    {action.label}
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

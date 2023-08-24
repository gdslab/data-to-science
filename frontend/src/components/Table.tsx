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
    <tbody className="divide-y divide-gray-200">
      {rows.map((row, i) => (
        <tr key={`row-${i}`}>
          {row.map((value, j) => (
            <td
              key={`cell-${i},${j}`}
              className="border border-slate-300 p-4 text-slate-500"
            >
              {value}
            </td>
          ))}
          {actions ? (
            <td className="border border-slate-300 p-4 text-slate-500">
              <div className="flex items-center justify-between gap-8">
                {actions[i].map((action) => (
                  <Link key={action.key} to={action.url}>
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
    <thead className="bg-slate-50">
      <tr>
        {columns.map((col) => (
          <th
            key={col.replace(/\s+/g, '').toLowerCase()}
            className="w-1/2 border border-slate-300 font-semibold p-4 text-lg text-slate-900 text-left"
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
    <table className="table-auto border-separate border-spacing-1 w-full border border-slate-400">
      {children}
    </table>
  );
}

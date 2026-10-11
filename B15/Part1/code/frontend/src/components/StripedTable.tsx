import clsx from 'clsx';

const cellClass = (wrap: boolean) =>
  clsx(
    'px-4 py-2',
    wrap ? 'whitespace-normal wrap-anywhere align-top' : 'whitespace-nowrap'
  );

const Table = ({ children }: { children: React.ReactNode }) => (
  <table className="min-w-full divide-y-2 divide-gray-200 bg-white text-sm">
    {children}
  </table>
);

const TableCell = ({
  children,
  wrap = false,
}: {
  children: React.ReactNode;
  wrap?: boolean;
}) => <td className={cellClass(wrap)}>{children}</td>;

const TableHeader = ({ children }: { children: React.ReactNode }) => (
  <thead className="text-left">
    <tr>{children}</tr>
  </thead>
);

const TableHeaderCol = ({ children }: { children: React.ReactNode }) => (
  <th scope="col" className="whitespace-nowrap px-4 py-2 font-medium text-gray-900">
    {children}
  </th>
);

const TableHeaderRow = ({
  children,
  wrap = false,
}: {
  children: React.ReactNode;
  wrap?: boolean;
}) => (
  <th scope="row" className={cellClass(wrap)}>
    {children}
  </th>
);

const TableRow = ({
  label,
  value,
  wrap = false,
}: {
  label: string;
  value: string;
  wrap?: boolean;
}) => (
  <tr className="odd:bg-gray-50">
    <TableHeaderRow wrap={wrap}>{label}</TableHeaderRow>
    <TableCell wrap={wrap}>{value}</TableCell>
  </tr>
);

const TableBody = ({ children }: { children: React.ReactNode }) => (
  <tbody className="divide-y divide-gray-200 text-left">{children}</tbody>
);

const StripedTable = ({
  headers,
  values,
  wrap = false,
}: {
  headers: string[];
  values: { label: string; value: string }[];
  /** Wrap long labels and values instead of forcing horizontal scroll */
  wrap?: boolean;
}) => (
  <Table>
    <TableHeader>
      {headers.map((colName, index) => (
        <TableHeaderCol key={`tablecol::${index}`}>{colName}</TableHeaderCol>
      ))}
    </TableHeader>
    <TableBody>
      {values.map(({ label, value }, index) => (
        <TableRow
          key={`tablerow::${index}`}
          label={label}
          value={value}
          wrap={wrap}
        />
      ))}
    </TableBody>
  </Table>
);

export default StripedTable;
export { Table, TableHeader, TableHeaderCol, TableBody, TableRow };

const Table = ({ children }: { children: React.ReactNode }) => (
  <table className="min-w-full divide-y-2 divide-gray-200 bg-white text-sm">
    {children}
  </table>
);

const TableCell = ({ children }: { children: React.ReactNode }) => (
  <td className="whitespace-nowrap px-4 py-2">{children}</td>
);

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

const TableHeaderRow = ({ children }: { children: React.ReactNode }) => (
  <th scope="row" className="whitespace-nowrap px-4 py-2">
    {children}
  </th>
);

const TableRow = ({ label, value }: { label: string; value: string }) => (
  <tr className="odd:bg-gray-50">
    <TableHeaderRow>{label}</TableHeaderRow>
    <TableCell>{value}</TableCell>
  </tr>
);

const TableBody = ({ children }: { children: React.ReactNode }) => (
  <tbody className="divide-y divide-gray-200 text-left">{children}</tbody>
);

const StripedTable = ({
  headers,
  values,
}: {
  headers: string[];
  values: { label: string; value: string }[];
}) => (
  <Table>
    <TableHeader>
      {headers.map((colName, index) => (
        <TableHeaderCol key={`tablecol::${index}`}>{colName}</TableHeaderCol>
      ))}
    </TableHeader>
    <TableBody>
      {values.map(({ label, value }, index) => (
        <TableRow key={`tablerow::${index}`} label={label} value={value} />
      ))}
    </TableBody>
  </Table>
);

export default StripedTable;
export { Table, TableHeader, TableHeaderCol, TableBody, TableRow };

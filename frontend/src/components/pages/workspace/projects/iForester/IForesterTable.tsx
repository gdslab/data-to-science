import { IForester } from '../Project';
import IForesterDeleteModal from './IForesterDeleteModal';

const HeaderCell = ({ children }: { children: React.ReactNode }) => <th>{children}</th>;

const Cell = ({
  children,
  extraStyles = '',
}: {
  children: React.ReactNode;
  extraStyles?: string;
}) => <td className={`mx-1 my-2 ${extraStyles}`}>{children}</td>;

export default function IForesterTable({ data }: { data: IForester[] }) {
  if (data.length === 0) return null;
  return (
    <table className="border-separate border-spacing-y-1 border-spacing-x-1">
      <thead>
        <tr className="h-12 sticky top-0 text-slate-700 bg-slate-300">
          <HeaderCell>Collection Date</HeaderCell>
          <HeaderCell>DBH</HeaderCell>
          <HeaderCell>Distance</HeaderCell>
          <HeaderCell>Latitude</HeaderCell>
          <HeaderCell>Longitude</HeaderCell>
          <HeaderCell>Note</HeaderCell>
          <HeaderCell>Phone direction</HeaderCell>
          <HeaderCell>Phone ID</HeaderCell>
          <HeaderCell>Species</HeaderCell>
          <HeaderCell>User</HeaderCell>
          <HeaderCell>Actions</HeaderCell>
        </tr>
      </thead>
      <tbody>
        {data.map((submission) => (
          <tr key={submission.id}>
            <Cell>{`${new Date(submission.timeStamp).toLocaleDateString()} ${new Date(
              submission.timeStamp
            ).toLocaleTimeString()}`}</Cell>
            <Cell>{submission.dbh.toFixed(2)}</Cell>
            <Cell>{submission.distance.toFixed(2)}</Cell>
            <Cell>{submission.latitude.toFixed(5)}</Cell>
            <Cell>{submission.longitude.toFixed(5)}</Cell>
            <Cell extraStyles="line-clamp-2">{submission.note}</Cell>
            <Cell>{submission.phoneDirection}</Cell>
            <Cell>{submission.phoneID}</Cell>
            <Cell>{submission.species}</Cell>
            <Cell>{submission.user}</Cell>
            <Cell>
              <IForesterDeleteModal iforester={submission} tableView={true} />
            </Cell>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

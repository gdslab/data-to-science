import IForesterCard from './IForesterCard';
import { IForester } from '../Project';

export default function IForesterList({ data }: { data: IForester[] }) {
  if (data.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-4 pb-24 overflow-y-auto">
      {data.map((submission) => (
        <IForesterCard key={submission.id} submission={submission} />
      ))}
    </div>
  );
}

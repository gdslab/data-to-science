import { ChangeEvent, useState } from 'react';

import { IForester } from '../Project';
import Card from '../../../../Card';
import IForesterMiniMap from './IForesterMiniMap';
import IForesterDeleteModal from './IForesterDeleteModal';

export default function IForesterCard({ submission }: { submission: IForester }) {
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);

  function handleDetailsToggle(e: ChangeEvent<HTMLDetailsElement>) {
    setIsDetailsOpen(e.target.open);
  }

  return (
    <Card
      rounded={true}
      title={`${new Date(submission.timeStamp).toLocaleDateString()} ${new Date(
        submission.timeStamp
      ).toLocaleTimeString()}`}
    >
      <div className="flex items-center justify-between gap-4">
        <img src={submission.depthFile} className="h-64 w-64" />
        <img src={submission.imageFile} className="h-64 w-64" />
      </div>
      <details onToggle={handleDetailsToggle}>
        <summary>Details</summary>
        <article>
          <IForesterMiniMap
            location={[submission.latitude, submission.longitude]}
            isDetailsOpen={isDetailsOpen}
          />
          <div className="flex flex-start gap-4">
            <span className="font-semibold text-gray-600">DBH</span>
            <span>{submission.dbh.toFixed(3)}</span>
          </div>
          <div className="flex flex-start gap-4">
            <span className="font-semibold text-gray-600">Distance</span>
            <span>{submission.distance.toFixed(3)}</span>
          </div>
          <div className="flex flex-start gap-4">
            <span className="font-semibold text-gray-600">Note</span>
            <span>{submission.note}</span>
          </div>
          <div className="flex flex-start gap-4">
            <span className="font-semibold text-gray-600">Phone direction</span>
            <span>{submission.phoneDirection}</span>
          </div>
          <div className="flex flex-start gap-4">
            <span className="font-semibold text-gray-600">Phone ID</span>
            <span>{submission.phoneID}</span>
          </div>
          <div className="flex flex-start gap-4">
            <span className="font-semibold text-gray-600">Species</span>
            <span>{submission.species}</span>
          </div>
          <div className="flex flex-start gap-4">
            <span className="font-semibold text-gray-600">User</span>
            <span>{submission.user}</span>
          </div>
        </article>
      </details>
      <div className="flex justify-end">
        <IForesterDeleteModal iforester={submission} />
      </div>
    </Card>
  );
}

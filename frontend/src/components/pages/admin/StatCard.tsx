import { StorageAvailability } from './DashboardTypes';

export default function StatCard({ title, value }: { title: string; value: number }) {
  return (
    <div className="flex flex-col rounded-lg bg-blue-50 px-4 py-8 text-center">
      <dt className="order-last text-lg font-medium text-gray-500">{title}</dt>

      <dd className="text-4xl font-extrabold text-blue-600 md:text-5xl">{value}</dd>
    </div>
  );
}

export function StatStorageCard({
  title,
  storage,
}: {
  title: string;
  storage: StorageAvailability;
}) {
  return (
    <div className="flex flex-col rounded-lg bg-blue-50 px-4 py-8 text-center">
      <dt className="order-last text-lg font-medium text-gray-500">{title}</dt>
      <div className="w-full h-4 mb-4 bg-gray-200 rounded-full dark:bg-gray-700">
        <div
          className="h-4 bg-blue-600 rounded-full dark:bg-blue-500"
          style={{ width: `${Math.round((storage.used / storage.total) * 100)}%` }}
        ></div>
      </div>
      <dt className="flex flex-row gap-2 order-last text-sm font-medium text-gray-500">
        <span>Used: {storage.used}</span>
        <span>Free: {storage.free}</span>
        <span>Total: {storage.total}</span>
      </dt>
    </div>
  );
}

import { useMemo, useState } from 'react';

import { StorageAvailability } from './DashboardTypes';

const TB_FACTOR = 1_000_000_000_000;
const GB_FACTOR = 1_000_000_000;

export default function StatCard({
  title,
  value,
  subtitle,
}: {
  title: string;
  value: number;
  subtitle?: string;
}) {
  return (
    <div className="flex flex-col rounded-lg bg-blue-50 px-4 py-8 text-center min-w-64">
      <dt className="order-last text-lg font-medium text-gray-500">{title}</dt>

      <dd className="text-4xl font-extrabold text-blue-600 md:text-5xl">
        {value}
      </dd>

      {subtitle && (
        <dd className="mt-1 text-sm text-gray-600">{subtitle}</dd>
      )}
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
  const [storageUnit, setStorageUnit] = useState<'gb' | 'tb'>('tb');

  const storageUnitLabel = storageUnit === 'gb' ? 'GB' : 'TB';

  const storageConverted = useMemo(() => {
    const factor = storageUnit === 'tb' ? TB_FACTOR : GB_FACTOR;
    return {
      used: storage.used / factor,
      free: storage.free / factor,
      total: storage.total / factor,
    };
  }, [storageUnit, storage]);

  const progressPercent = storageConverted.total
    ? Math.round((storageConverted.used / storageConverted.total) * 100)
    : 0;

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value as 'gb' | 'tb';
    setStorageUnit(value);
  };

  return (
    <div className="flex flex-col rounded-lg bg-blue-50 px-4 py-8 text-center min-w-64">
      <dt className="order-last text-lg font-medium text-gray-500">
        {title} ({storageUnitLabel})
      </dt>
      <div className="w-full h-4 mb-4 bg-gray-200 rounded-full">
        <div
          className="h-4 bg-blue-600 rounded-full"
          style={{
            width: `${progressPercent}%`,
          }}
        ></div>
      </div>
      <dt className="flex flex-row mt-2 gap-2 order-last justify-center text-sm font-medium text-gray-500">
        <div className="flex flex-col gap-1.5 w-20">
          <span>Used:</span>
          <span>{storageConverted.used.toFixed(2)}</span>
        </div>
        <div className="flex flex-col gap-1.5 w-20">
          <span>Free:</span>
          <span>{storageConverted.free.toFixed(2)}</span>
        </div>
        <div className="flex flex-col gap-1.5 w-20">
          <span>Total:</span>
          <span>{storageConverted.total.toFixed(2)}</span>
        </div>
      </dt>
      <dt className="flex flex-row mt-4 gap-2 order-last items-center text-sm font-medium text-gray-500">
        Storage Unit:
        <input
          id="gb"
          type="radio"
          name="storageUnit"
          value="gb"
          checked={storageUnit === 'gb'}
          onChange={handleChange}
        />
        <label htmlFor="gb">GB</label>
        <input
          id="tb"
          type="radio"
          name="storageUnit"
          value="tb"
          checked={storageUnit === 'tb'}
          onChange={handleChange}
        />
        <label htmlFor="tb">TB</label>
      </dt>
    </div>
  );
}

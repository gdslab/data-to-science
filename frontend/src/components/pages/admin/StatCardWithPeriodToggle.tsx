import { useState } from 'react';

type Period = 30 | 60 | 90 | 365;

interface PeriodOption {
  value: Period;
  label: string;
  title: string;
}

const PERIOD_OPTIONS: PeriodOption[] = [
  { value: 30, label: '30 days', title: 'Last 30 days' },
  { value: 60, label: '60 days', title: 'Last 60 days' },
  { value: 90, label: '90 days', title: 'Last 90 days' },
  { value: 365, label: '1 year', title: 'Last year' },
];

export default function StatCardWithPeriodToggle({
  getValue,
}: {
  getValue: (period: Period) => number;
}) {
  const [selectedPeriod, setSelectedPeriod] = useState<Period>(30);

  const currentOption = PERIOD_OPTIONS.find((opt) => opt.value === selectedPeriod);
  const value = getValue(selectedPeriod);

  return (
    <div className="relative flex flex-col rounded-lg bg-blue-50 px-4 py-8 text-center min-w-64">
      <div className="absolute top-2 right-2">
        <select
          value={selectedPeriod}
          onChange={(e) => setSelectedPeriod(Number(e.target.value) as Period)}
          className="text-xs bg-white border border-gray-300 rounded pl-2 pr-7 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {PERIOD_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <dt className="order-last text-lg font-medium text-gray-500">
        {currentOption?.title}
      </dt>

      <dd className="text-4xl font-extrabold text-blue-600 md:text-5xl">
        {value}
      </dd>
    </div>
  );
}

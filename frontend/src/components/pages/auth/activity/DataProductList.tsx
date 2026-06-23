import { ReactNode } from 'react';

export default function DataProductList({
  title,
  isEmpty,
  emptyMessage = 'Nothing here yet.',
  children,
}: {
  title: string;
  isEmpty: boolean;
  emptyMessage?: string;
  children: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-2">
      <span className="text-xs font-medium uppercase tracking-wide text-gray-500">
        {title}
      </span>
      {isEmpty ? (
        <p className="text-sm text-gray-500">{emptyMessage}</p>
      ) : (
        <div className="flex flex-col">{children}</div>
      )}
    </div>
  );
}

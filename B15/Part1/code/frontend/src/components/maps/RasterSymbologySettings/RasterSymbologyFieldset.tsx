import { ReactNode } from 'react';

export default function RasterSymbologyFieldSet({
  children,
  title,
}: {
  children: ReactNode;
  title: string;
}) {
  return (
    <fieldset className="border border-solid border-slate-300 p-3">
      <legend className="block text-sm text-gray-400 font-bold pt-2 pb-1">
        {title}
      </legend>
      {children}
    </fieldset>
  );
}

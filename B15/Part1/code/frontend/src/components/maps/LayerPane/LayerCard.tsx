import clsx from 'clsx';

export default function LayerCard({
  active = false,
  bg = 'bg-white',
  children,
  hover = false,
  ...props
}: {
  active?: boolean;
  bg?: string;
  children: React.ReactNode;
  hover?: boolean;
  [key: string]: unknown;
}) {
  return (
    <div
      className={clsx(
        `p-2 rounded-xs shadow-xs ${bg} border-solid border-2`,
        {
          'border-slate-400': active,
          'border-slate-200': !active,
          'cursor-pointer hover:border-2 hover:shadow-md': hover && !active,
        }
      )}
      {...props}
    >
      {children}
    </div>
  );
}

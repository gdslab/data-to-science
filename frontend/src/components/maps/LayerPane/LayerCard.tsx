import clsx from 'clsx';

export default function LayerCard({
  active = false,
  children,
  hover = false,
  ...props
}: {
  active?: boolean;
  children: React.ReactNode;
  hover?: boolean;
  [key: string]: any;
}) {
  return (
    <div
      className={clsx(
        'p-2 rounded-xs shadow-xs bg-white border-solid border-2',
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

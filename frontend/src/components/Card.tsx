import { classNames } from './utils';

export default function Card({
  children,
  rounded = false,
  title,
}: {
  children: React.ReactNode;
  rounded?: boolean;
  title?: string;
}) {
  return (
    <div
      className={classNames(
        rounded ? 'rounded-lg' : 'rounded-sm',
        'p-8 drop-shadow-md bg-white'
      )}
    >
      {title ? <h1 className="mb-8 text-accent3">{title}</h1> : null}
      {children}
    </div>
  );
}

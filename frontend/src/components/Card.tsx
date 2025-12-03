import { classNames } from './utils';

export default function Card({
  children,
  backgroundColor = 'white',
  rounded = false,
  title,
}: {
  children: React.ReactNode;
  backgroundColor?: string;
  rounded?: boolean;
  title?: string;
}) {
  return (
    <div
      className={classNames(
        rounded ? 'rounded-lg' : 'rounded-xs',
        classNames(
          backgroundColor === 'accent2' ? 'bg-accent2/20' : 'bg-white',
          'p-4 drop-shadow-md'
        )
      )}
    >
      {title ? <h1 className="mb-8 text-accent3">{title}</h1> : null}
      {children}
    </div>
  );
}

export default function Card({
  children,
  title,
}: {
  children: React.ReactNode;
  title?: string;
}) {
  return (
    <div className="p-8 rounded-sm drop-shadow-md bg-white">
      {title ? <h1 className="mb-8 text-accent3">{title}</h1> : null}
      {children}
    </div>
  );
}

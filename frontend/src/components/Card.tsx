export default function Card({ children }: { children: React.ReactNode }) {
  return <div className="m-4 p-8 rounded-md drop-shadow-md bg-white">{children}</div>;
}

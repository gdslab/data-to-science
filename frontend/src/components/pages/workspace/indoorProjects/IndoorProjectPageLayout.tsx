import { IndoorProjectProvider } from './IndoorProjectContext';

export default function IndoorProjectPageLayout({ children }) {
  return (
    <IndoorProjectProvider>
      <div className="mx-4 my-2 flex flex-col gap-2">{children}</div>
    </IndoorProjectProvider>
  );
}

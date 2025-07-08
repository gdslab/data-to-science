import { IndoorProjectProvider } from './IndoorProjectContext';

export default function IndoorProjectPageLayout({ children }) {
  return (
    <IndoorProjectProvider>
      <div className="h-full mx-4 py-2 flex flex-col gap-2">{children}</div>
    </IndoorProjectProvider>
  );
}

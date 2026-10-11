import Card from '../../Card';
import Welcome from '../Welcome';

type Layout = {
  children: React.ReactNode;
  pageTitle: string;
};

export default function Layout({ children, pageTitle }: Layout) {
  return (
    <div className="h-screen bg-accent1">
      <div className="flex flex-wrap items-center justify-center">
        <div className="sm:w-full md:w-1/2 lg:w-2/5 max-w-3xl mx-4">
          <Welcome>{pageTitle}</Welcome>
          <Card>{children}</Card>
        </div>
      </div>
    </div>
  );
}

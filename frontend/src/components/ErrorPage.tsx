import { Link, isRouteErrorResponse, useRouteError } from 'react-router-dom';

export default function ErrorPage() {
  const error = useRouteError();
  console.error(error);

  return (
    <div className="flex flex-col w-full items-center justify-center">
      <h1>Oops!</h1>
      <p>Sorry, an unexpected error has occurred.</p>
      <p>
        <em>{isRouteErrorResponse(error) ? error.statusText : 'Not found'}</em>
      </p>
      <Link to="/home">Return Home</Link>
    </div>
  );
}

import { Link, isRouteErrorResponse, useRouteError } from "react-router-dom";

export default function ErrorPage() {
  const error = useRouteError();
  console.error(error);

  return (
    <div id="error-page">
      <h1>Oops!</h1>
      <p>Sorry, an unexpected error has occurred.</p>
      <p>
        <em>{isRouteErrorResponse(error) ? error.statusText : "Not found"}</em>
      </p>
      <Link to="/">Return Home</Link>
    </div>
  );
}

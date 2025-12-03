import axios from 'axios';
import { useEffect } from 'react';
import {
  Link,
  isRouteErrorResponse,
  useNavigate,
  useRouteError,
} from 'react-router-dom';

export default function ErrorPage() {
  const navigate = useNavigate();
  const error = useRouteError();
  let statusCode: number | undefined = 404;

  useEffect(() => {
    if (axios.isAxiosError(error)) {
      statusCode = error.response?.status;
      if (
        (error.response?.status === 404 &&
          error.response?.data.detail === 'Account not found') ||
        error.response?.status === 403 ||
        error.response?.status === 401
      ) {
        navigate('/auth/login');
      }
    }
  }, [error]);

  return (
    <div className="grid h-screen px-4 bg-white place-content-center">
      <div className="text-center">
        <h1 className="font-black text-gray-200 text-9xl">
          {statusCode ? statusCode.toString() : '404'}
        </h1>

        <p className="text-2xl font-bold tracking-tight text-gray-900 sm:text-4xl">
          Uh-oh!
        </p>

        <p className="mt-4 text-gray-500">
          {isRouteErrorResponse(error)
            ? error.statusText
            : axios.isAxiosError(error)
            ? error.response?.data.detail
            : "We can't find that page."}
        </p>

        <div className="flex items-center justify-between gap-4">
          <Link
            to="/home"
            className="inline-block w-36 px-5 py-3 mt-6 text-sm font-medium text-white bg-accent3 rounded-sm hover:bg-accent2 focus:outline-hidden focus:ring-3"
          >
            Go Back Home
          </Link>

          <Link
            to="/auth/logout"
            className="inline-block w-36 px-5 py-3 mt-6 text-sm font-medium text-white bg-accent3 rounded-sm hover:bg-accent2 focus:outline-hidden focus:ring-3"
          >
            Logout
          </Link>
        </div>
      </div>
    </div>
  );
}

import { useContext, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import AuthContext from '../AuthContext';
import { Button } from './Buttons';
import landingVideo from '../assets/landing.mp4';

export default function Landing() {
  const { user } = useContext(AuthContext);
  const navigate = useNavigate();
  useEffect(() => {
    if (user) {
      navigate('/home');
    }
  }, []);
  return !user ? (
    <div className="h-full flex flex-wrap">
      {/* video pane */}
      <div className="flex min-h-min w-full md:basis-3/5 basis-1/1 bg-primary items-center justify-center">
        <div className="h-96 flex items-center justify-center">
          <div className="mx-4 border-4 border-slate-200">
            <video controls>
              <source src={landingVideo} type="video/mp4" />
            </video>
          </div>
        </div>
      </div>
      {/* sign up pane */}
      <div className="flex md:basis-2/5 basis-1/1 bg-accent1 justify-center p-4">
        <div className="flex flex-col items-center justify-center gap-4">
          <div className="flex items-center justify-center gap-4">
            <div className="h-16 w-16 bg-accent2 flex items-center justify-center">
              Logo
            </div>
            <div>
              <h1 className="mb-0">{import.meta.env.VITE_BRAND_FULL}</h1>
            </div>
          </div>
          <div className="m-4">
            <em className="text-secondary font-bold">
              SloganSloganSloganSloganSlogan!
            </em>
          </div>
          <div className="mt-8">
            Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod
            tempor incididunt ut labore et dolore magna aliqua. Praesent tristique magna
            sit amet purus gravida quis blandit. Vitae semper quis lectus nulla. Arcu
            non sodales neque sodales ut etiam sit.
          </div>
          <div className="w-full mt-16">
            <Link to="/auth/register">
              <Button icon="arrow">Sign up to join!</Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  ) : null;
}

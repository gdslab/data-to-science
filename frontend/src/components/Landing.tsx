import { useContext, useEffect } from 'react';
import { Link, useNavigate } from 'react-router';

import AuthContext from '../AuthContext';
import { Button, LandingButton } from './Buttons';

import brandLogo from '../assets/d2s-logo-amber-text-white-symbol.svg';
import landingVideo from '../assets/landing.mp4';

export default function Landing() {
  const { user } = useContext(AuthContext);
  const navigate = useNavigate();
  useEffect(() => {
    if (user) {
      navigate('/home');
    }
  }, [navigate, user]);

  return !user ? (
    <div className="grid grid-flow-row auto-rows-max">
      {/* video pane */}
      <div className="h-screen">
        <div className="z-10 absolute w-full px-4 text-center top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
          <div className="grid grid-rows-auto gap-6">
            <div className="inline text-6xl text-white [text-shadow:2px_2px_2px_rgb(0_0_0/70%)]">
              <span>Welcome to </span>
            </div>
            <div className="flex items-center justify-center">
              <img
                className="h-24 text-amber-400"
                src={brandLogo}
                alt="Brand Logo"
              />
            </div>
            <div className="flex items-center justify-center">
              <span className="text-white font-semibold">
                {import.meta.env.VITE_BRAND_SLOGAN}
              </span>
            </div>
          </div>
          <div className="mt-16 flex items-center justify-center gap-16">
            <div className="w-full md:w-1/4">
              <Link to="/auth/register">
                <Button>Sign up</Button>
              </Link>
            </div>
            <div className="w-full md:w-1/4">
              <Link to="/auth/login">
                <LandingButton>Sign in</LandingButton>
              </Link>
            </div>
          </div>
        </div>
        <video
          className="w-full h-full object-cover opacity-80"
          autoPlay
          loop
          muted
        >
          <source src={landingVideo} type="video/mp4" />
          <div className="sr-only">
            Overhead video of field captured by a UAS
          </div>
        </video>
      </div>
      {/* sign up pane */}
    </div>
  ) : null;
}

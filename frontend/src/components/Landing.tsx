import { useContext, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import AuthContext from '../AuthContext';
import { Button, OutlineButton } from './Buttons';

import brandLogo from '../assets/d2s-logo-white.png';
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
    <div className="grid grid-flow-row auto-rows-max">
      {/* video pane */}
      <div className="h-screen">
        <div className="z-10 absolute w-full text-center top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
          <div className="grid grid-rows-auto gap-4">
            <div className="flex items-center justify-center">
              <img className="h-28 w-28" src={brandLogo} alt="Brand Logo" />
            </div>
            <div className="inline text-6xl text-white font-bold [text-shadow:_2px_2px_2px_rgb(0_0_0_/_70%)]">
              <span>Welcome to </span>
              <span className="text-amber-400">{import.meta.env.VITE_BRAND_FULL}</span>
            </div>
            <div className="flex items-center justify-center">
              <span className="text-white font-semibold">
                {import.meta.env.VITE_BRAND_SLOGAN}
              </span>
            </div>
          </div>
          <div className="mt-16 flex items-center justify-center gap-16">
            <div className="w-1/4">
              <Link to="/auth/register">
                <Button>Sign up</Button>
              </Link>
            </div>
            <div className="w-1/4">
              <Link to="/auth/login">
                <OutlineButton color="white">Sign in</OutlineButton>
              </Link>
            </div>
          </div>
        </div>
        <video className="w-full h-full object-cover opacity-80" autoPlay loop muted>
          <source src={landingVideo} type="video/mp4" />
          <div className="sr-only">Overhead video of field captured by a UAS</div>
        </video>
      </div>
      {/* sign up pane */}
    </div>
  ) : null;
}

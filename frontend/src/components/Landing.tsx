import { useContext, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import AuthContext from '../AuthContext';
import { Button } from './Buttons';

import brandLogo from '../assets/d2s-logo-black.png';
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
      <div>
        <div className="z-10 absolute top-1/2 w-full text-center">
          <span className="text-7xl text-accent1 font-bold [text-shadow:_2px_2px_2px_rgb(0_0_0_/_70%)]">
            Welcome to {import.meta.env.VITE_BRAND_FULL}
          </span>
        </div>
        <video className="h-full h-screen object-none opacity-70" autoPlay loop>
          <source src={landingVideo} type="video/mp4" />
          <div className="sr-only">Overhead video of field captured by a UAS</div>
        </video>
      </div>
      {/* sign up pane */}
      <div className="bg-accent1 p-8">
        <div className="grid grid-rows-3 gap-4">
          <div className="flex items-center justify-center">
            <img className="h-24 w-24" src={brandLogo} alt="Brand Logo" />
          </div>
          <div className="flex items-center justify-center">
            <em className="text-accent3 text-2xl font-bold">
              {import.meta.env.VITE_BRAND_SLOGAN}
            </em>
          </div>
          <div className="flex items-center justify-center">
            <div className="w-1/2">
              <Link to="/auth/register">
                <Button icon="arrow">Sign up to join!</Button>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  ) : null;
}

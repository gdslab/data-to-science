import { useContext, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import AuthContext from '../AuthContext';
import { Button } from './Buttons';

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
          <span className="text-xl font-extrabold">Video</span>
        </div>
      </div>
      {/* sign up pane */}
      <div className="flex md:basis-2/5 basis-1/1 bg-accent1 justify-center p-4">
        <div className="flex flex-col items-center justify-center gap-4">
          <div className="flex items-center justify-center gap-4">
            <div className="h-16 w-16 bg-accent2 text-white flex items-center justify-center">
              Logo
            </div>
            <div>
              <h1 className="text-white mb-0">System Name</h1>
            </div>
          </div>
          <div className="m-4">
            <em className="text-secondary font-bold">
              SloganSloganSloganSloganSlogan!
            </em>
          </div>
          <div className="mt-8 text-white">
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

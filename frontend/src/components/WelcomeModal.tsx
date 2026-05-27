import { Fragment, useContext, useState } from 'react';
import { Dialog, DialogPanel, Transition, TransitionChild } from '@headlessui/react';
import { Link, useNavigate } from 'react-router';
import { FaMap, FaRightToBracket, FaUserPlus } from 'react-icons/fa6';

import AuthContext from '../AuthContext';
import d2sLogo from '../assets/d2s-logo-blue.svg';

const STORAGE_KEY = 'exploreWelcomeDismissed';

function IconBox({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-slate-200 text-primary">
      {children}
    </div>
  );
}

export default function WelcomeModal() {
  const { user } = useContext(AuthContext);
  const navigate = useNavigate();
  const [open, setOpen] = useState(
    () => !user && localStorage.getItem(STORAGE_KEY) !== 'true'
  );

  function dismiss() {
    localStorage.setItem(STORAGE_KEY, 'true');
    setOpen(false);
  }

  function dismissAndNavigate(path: string) {
    localStorage.setItem(STORAGE_KEY, 'true');
    setOpen(false);
    navigate(path);
  }

  return (
    <Transition show={open} as={Fragment}>
      <Dialog as="div" className="relative z-20" onClose={dismiss}>
        <TransitionChild
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/60 transition-opacity" />
        </TransitionChild>

        <div className="fixed inset-0 z-10 flex items-center justify-center p-4">
          <TransitionChild
            as={Fragment}
            enter="ease-out duration-300"
            enterFrom="opacity-0 scale-95"
            enterTo="opacity-100 scale-100"
            leave="ease-in duration-200"
            leaveFrom="opacity-100 scale-100"
            leaveTo="opacity-0 scale-95"
          >
            <DialogPanel className="w-full max-w-md rounded-xl bg-slate-100 p-6 shadow-2xl">
              {/* Header */}
              <div className="flex justify-center mb-4">
                <img src={d2sLogo} alt="Data to Science" className="h-10" />
              </div>

              {/* Subtitle */}
              <p className="text-sm text-gray-600 mb-6">
                Welcome to {import.meta.env.VITE_BRAND_FULL}, an open-source
                web platform for transforming environmental and geospatial data
                into interactive scientific workflows, visualizations, and
                analyses. Explore, process, and share complex spatial data
                through a scalable, browser-based interface.
              </p>

              {/* Feature rows */}
              <div className="flex flex-col gap-4 mb-6">
                <button
                  type="button"
                  className="flex items-center gap-4 text-left group"
                  onClick={() => dismissAndNavigate('/auth/register')}
                >
                  <IconBox>
                    <FaUserPlus className="h-4 w-4" />
                  </IconBox>
                  <div>
                    <p className="text-sm font-semibold text-gray-900 group-hover:text-primary transition-colors">
                      Sign up
                    </p>
                    <p className="text-xs text-gray-500">
                      Create a free account to upload and manage your own projects.
                    </p>
                  </div>
                </button>

                <button
                  type="button"
                  className="flex items-center gap-4 text-left group"
                  onClick={() => dismissAndNavigate('/auth/login')}
                >
                  <IconBox>
                    <FaRightToBracket className="h-4 w-4" />
                  </IconBox>
                  <div>
                    <p className="text-sm font-semibold text-gray-900 group-hover:text-primary transition-colors">
                      Log in
                    </p>
                    <p className="text-xs text-gray-500">
                      Access your workspace and continue working on your projects.
                    </p>
                  </div>
                </button>

                <button
                  type="button"
                  className="flex items-center gap-4 text-left group"
                  onClick={dismiss}
                >
                  <IconBox>
                    <FaMap className="h-4 w-4" />
                  </IconBox>
                  <div>
                    <p className="text-sm font-semibold text-gray-900 group-hover:text-primary transition-colors">
                      Explore
                    </p>
                    <p className="text-xs text-gray-500">
                      Browse publicly shared data products — no account needed.
                    </p>
                  </div>
                </button>
              </div>

              {/* Buttons */}
              <div className="flex gap-3">
                <Link
                  to="/auth/register"
                  onClick={() => localStorage.setItem(STORAGE_KEY, 'true')}
                  className="flex-1 rounded-md bg-amber-400 py-2 text-center text-sm font-semibold text-black hover:bg-amber-300 transition-colors"
                >
                  Get started
                </Link>
                <button
                  type="button"
                  onClick={dismiss}
                  className="flex-1 rounded-md border border-gray-300 py-2 text-sm font-semibold text-gray-600 hover:bg-slate-200 transition-colors"
                >
                  Explore as guest
                </button>
              </div>


            </DialogPanel>
          </TransitionChild>
        </div>
      </Dialog>
    </Transition>
  );
}

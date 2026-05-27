import { useContext, useState } from 'react';
import { Dialog, DialogPanel, DialogTitle, Transition, TransitionChild } from '@headlessui/react';
import { useNavigate } from 'react-router';
import { FaMap, FaRightToBracket, FaUserPlus } from 'react-icons/fa6';

import AuthContext from '../AuthContext';
import d2sLogo from '../assets/d2s-logo-blue.svg';
import Checkbox from './Checkbox';

function IconBox({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary text-white">
      {children}
    </div>
  );
}

export default function WelcomeModal() {
  const { user } = useContext(AuthContext);
  const navigate = useNavigate();
  const [open, setOpen] = useState(
    () => !user && localStorage.getItem('hideWelcomeModal') !== 'true'
  );
  const [dontShowAgain, setDontShowAgain] = useState(false);

  function dismiss() {
    if (dontShowAgain) {
      localStorage.setItem('hideWelcomeModal', 'true');
    }
    setOpen(false);
  }

  function dismissAndNavigate(path: string) {
    if (dontShowAgain) {
      localStorage.setItem('hideWelcomeModal', 'true');
    }
    setOpen(false);
    navigate(path);
  }

  return (
    <Transition show={open}>
      <Dialog as="div" className="relative z-20" onClose={dismiss}>
        <TransitionChild
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/60 transition-opacity" />
        </TransitionChild>

        <div className="fixed inset-0 z-10 flex items-center justify-center overflow-y-auto p-4">
          <TransitionChild
            enter="ease-out duration-300"
            enterFrom="opacity-0 scale-95"
            enterTo="opacity-100 scale-100"
            leave="ease-in duration-200"
            leaveFrom="opacity-100 scale-100"
            leaveTo="opacity-0 scale-95"
          >
            <DialogPanel className="w-full max-w-md rounded-xl bg-slate-100 p-6 shadow-2xl">
              <DialogTitle className="sr-only">
                Welcome to {import.meta.env.VITE_BRAND_FULL ?? 'Data to Science'}
              </DialogTitle>

              {/* Header */}
              <div className="flex justify-center mb-4">
                <img src={d2sLogo} alt="Data to Science" className="h-10" />
              </div>

              {/* Subtitle */}
              <p className="text-sm text-gray-600 mb-6">
                Welcome to {import.meta.env.VITE_BRAND_FULL ?? 'Data to Science'}, an open-source
                web platform for transforming environmental and geospatial data
                into interactive scientific workflows, visualizations, and
                analyses. Explore, process, and share complex spatial data
                through a scalable, browser-based interface.
              </p>

              {/* Feature rows */}
              <div className="flex flex-col gap-4">
                <button
                  type="button"
                  className="flex items-center gap-4 text-left group w-full rounded-lg border border-gray-200 bg-white p-3 shadow-sm hover:shadow-md hover:border-gray-300 transition-all"
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
                  className="flex items-center gap-4 text-left group w-full rounded-lg border border-gray-200 bg-white p-3 shadow-sm hover:shadow-md hover:border-gray-300 transition-all"
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
                  className="flex items-center gap-4 text-left group w-full rounded-lg border border-gray-200 bg-white p-3 shadow-sm hover:shadow-md hover:border-gray-300 transition-all"
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

              {/* Don't show again */}
              <div className="mt-4 flex items-center">
                <Checkbox
                  id="dont-show-welcome"
                  checked={dontShowAgain}
                  onChange={(e) => setDontShowAgain(e.target.checked)}
                />
                <label
                  htmlFor="dont-show-welcome"
                  className="ms-2 text-sm font-medium text-gray-900"
                >
                  Don't show this again
                </label>
              </div>
            </DialogPanel>
          </TransitionChild>
        </div>
      </Dialog>
    </Transition>
  );
}

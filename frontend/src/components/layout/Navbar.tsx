import clsx from 'clsx';
import { Fragment, useContext } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Disclosure,
  DisclosureButton,
  DisclosurePanel,
  Menu,
  MenuButton,
  MenuItem,
  MenuItems,
  Transition,
} from '@headlessui/react';
import {
  Bars3Icon,
  ChevronDownIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';

import AuthContext from '../../AuthContext';
import ContactFormModal from '../ContactForm';
import { generateRandomProfileColor } from '../pages/auth/Profile';

import brandLogo from '../../assets/d2s-logo-white.svg';
import smallBrandLogo from '../../assets/d2s-logo-white.svg';

const navigation = [
  { name: 'HOMEPAGE', href: '/home' },
  { name: 'WORKSPACE', href: '/projects' },
  { name: 'MY TEAMS', href: '/teams' },
  { name: 'CONTACT US', component: <ContactFormModal /> },
];

const styles = {
  menuItem: 'block px-4 py-2 text-sm text-gray-700 visited:text-gray-700',
  inFocusMenuItem: 'bg-gray-100',
  outFocusMenuItem: '',
};

export default function Navbar() {
  const location = useLocation();
  const { user } = useContext(AuthContext);
  const showContact = import.meta.env.VITE_SHOW_CONTACT_FORM !== '0';

  return (
    <Disclosure as="nav" className="bg-primary overflow-x-clip">
      {({ open }) => (
        <>
          <div className="mx-auto px-2 sm:px-6 lg:px-8">
            <div className="relative flex h-16 items-center justify-between">
              <div className="w-full flex shrink-0 items-center justify-center md:hidden">
                <Link to="/">
                  <img
                    className="max-h-8 max-w-full h-auto object-contain"
                    src={smallBrandLogo}
                    alt="Brand logo"
                  />
                </Link>
              </div>
              {user ? (
                <div className="absolute inset-y-0 left-0 flex items-center md:hidden">
                  {/* Mobile menu button*/}
                  <DisclosureButton className="relative inline-flex items-center justify-center rounded-md p-2 text-white focus:bg-[#365173]">
                    <span className="absolute -inset-0.5" />
                    <span className="sr-only">Open main menu</span>
                    {open ? (
                      <XMarkIcon className="block h-6 w-6" aria-hidden="true" />
                    ) : (
                      <Bars3Icon className="block h-6 w-6" aria-hidden="true" />
                    )}
                  </DisclosureButton>
                </div>
              ) : null}
              <div className="h-full flex">
                <Link
                  className="min-w-40 flex items-center hidden md:flex"
                  to="/"
                >
                  <img
                    className="h-8 w-auto"
                    src={brandLogo}
                    alt="Brand logo"
                  />
                </Link>
                {user ? (
                  <div className="h-full hidden md:ml-6 md:block">
                    <div className="h-full flex items-center space-x-4">
                      {navigation
                        .filter(
                          (item) => showContact || item.name !== 'CONTACT US'
                        )
                        .map((item) => {
                          if (item.href) {
                            return (
                              <Link
                                key={item.name}
                                to={item.href}
                                className={clsx(
                                  'rounded-md px-3 py-2 text-md text-white visited:text-white',
                                  location.pathname === item.href
                                    ? 'font-semibold'
                                    : 'hover:[text-shadow:0px_8px_16px_rgb(0_0_0/70%)]'
                                )}
                                aria-current={
                                  location.pathname === item.href
                                    ? 'page'
                                    : undefined
                                }
                              >
                                {item.name}
                              </Link>
                            );
                          } else {
                            return <div key={item.name}>{item.component}</div>;
                          }
                        })}
                    </div>
                  </div>
                ) : null}
              </div>
              {user ? (
                <div className="h-full min-w-56 flex items-center justify-center lg:border-l-2 border-white">
                  <div className="absolute inset-y-0 right-0 flex items-center pr-2 lg:static lg:inset-auto lg:ml-6 lg:pr-0">
                    {/* Profile dropdown */}
                    <Menu as="div" className="relative ml-3 text-white">
                      <MenuButton className="relative flex rounded-full">
                        <span className="absolute -inset-1.5" />
                        <span className="sr-only">Open user menu</span>
                        <div className="flex items-center justify-center">
                          {user.profile_url ? (
                            <img
                              key={user.profile_url
                                .split('/')
                                .slice(-1)[0]
                                .slice(0, -4)}
                              className="h-8 w-8 rounded-full"
                              src={user.profile_url}
                            />
                          ) : (
                            <div
                              className="flex items-center justify-center h-8 w-8 text-sm rounded-full"
                              style={generateRandomProfileColor(
                                user.first_name + ' ' + user.last_name
                              )}
                            >
                              <span className="indent-[0.1em] tracking-widest">
                                {user.first_name[0] + user.last_name[0]}
                              </span>
                            </div>
                          )}

                          <div className="hidden lg:inline ml-4">
                            {user.first_name} {user.last_name}
                          </div>
                          <ChevronDownIcon
                            className="inline h-4 w-4 ml-2"
                            aria-hidden="true"
                          />
                        </div>
                      </MenuButton>
                      <Transition
                        as={Fragment}
                        enter="transition ease-out duration-100"
                        enterFrom="transform opacity-0 scale-95"
                        enterTo="transform opacity-100 scale-100"
                        leave="transition ease-in duration-75"
                        leaveFrom="transform opacity-100 scale-100"
                        leaveTo="transform opacity-0 scale-95"
                      >
                        <MenuItems className="absolute right-0 z-50 mt-2 w-48 origin-top-right rounded-md bg-white py-1 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-hidden">
                          <MenuItem>
                            {({ focus }) => (
                              <Link
                                to="/auth/profile"
                                className={clsx(
                                  styles.menuItem,
                                  focus
                                    ? styles.inFocusMenuItem
                                    : styles.outFocusMenuItem
                                )}
                              >
                                Your Profile
                              </Link>
                            )}
                          </MenuItem>
                          {user.is_superuser ? (
                            <MenuItem>
                              {({ focus }) => (
                                <Link
                                  to="/admin/dashboard"
                                  className={clsx(
                                    styles.menuItem,
                                    focus
                                      ? styles.inFocusMenuItem
                                      : styles.outFocusMenuItem
                                  )}
                                >
                                  Dashboard
                                </Link>
                              )}
                            </MenuItem>
                          ) : null}
                          <MenuItem>
                            {({ focus }) => (
                              <Link
                                to="/auth/logout"
                                className={clsx(
                                  styles.menuItem,
                                  focus
                                    ? styles.inFocusMenuItem
                                    : styles.outFocusMenuItem
                                )}
                              >
                                Sign out
                              </Link>
                            )}
                          </MenuItem>
                        </MenuItems>
                      </Transition>
                    </Menu>
                  </div>
                </div>
              ) : (
                <div className="h-full min-w-56 flex items-center justify-center border-l-2 border-white">
                  <div className="absolute inset-y-0 right-0 flex items-center text-white pr-2 sm:static sm:inset-auto sm:ml-6 sm:pr-0">
                    <Link to="/auth/login">Sign in</Link>
                  </div>
                </div>
              )}
            </div>
          </div>

          {user ? (
            <DisclosurePanel className="sm:hidden">
              <div className="space-y-1 px-2 pb-3 pt-2">
                {navigation.map((item) => {
                  if (item.href) {
                    return (
                      <DisclosureButton
                        key={item.name}
                        as="a"
                        href={item.href}
                        className={clsx(
                          'block rounded-md px-3 py-2 text-white visited:text-white hover:[text-shadow:0px_8px_16px_rgb(0_0_0/70%)]',
                          location.pathname === item.href
                            ? 'font-semibold'
                            : 'font-normal'
                        )}
                        aria-current={
                          location.pathname === item.href ? 'page' : undefined
                        }
                      >
                        {item.name}
                      </DisclosureButton>
                    );
                  } else {
                    return (
                      <div key={item.name} className="font-normal">
                        {item.component}
                      </div>
                    );
                  }
                })}
              </div>
            </DisclosurePanel>
          ) : null}
        </>
      )}
    </Disclosure>
  );
}

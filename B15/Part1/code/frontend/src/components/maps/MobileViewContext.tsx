import { createContext, useContext } from 'react';

type MobileView = 'map' | 'list';

const MobileViewContext = createContext<{
  setMobileView: (view: MobileView) => void;
}>({ setMobileView: () => {} });

export const MobileViewProvider = MobileViewContext.Provider;
export const useMobileView = () => useContext(MobileViewContext);

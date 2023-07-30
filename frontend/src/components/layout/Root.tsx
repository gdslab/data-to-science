import { Outlet } from 'react-router-dom';

import Footer from './Footer';
import Header from './Header';

export default function Root() {
  return (
    <div className="wrapper">
      <div className="header">
        <Header />
      </div>
      <div className="content">
        <Outlet />
      </div>
      <div className="footer">
        <Footer />
      </div>
    </div>
  );
}

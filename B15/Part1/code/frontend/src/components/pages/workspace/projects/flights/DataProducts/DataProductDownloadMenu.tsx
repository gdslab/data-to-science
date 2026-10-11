import { useState } from 'react';
import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/react';
import { ArrowDownTrayIcon, ChevronDownIcon } from '@heroicons/react/24/outline';
import clsx from 'clsx';

import { Status } from '../../../../../Alert';
import { exportDataProductToJpeg } from '../../../../../maps/utils';
import { isGeoTIFF } from './DataProductsTable';

import { DataProduct } from '../../Project';

const menuItemClasses =
  'flex w-full items-center px-4 py-2 text-left text-sm text-gray-700';

// Transparency has no equivalent in a JPG, so it is worth saying before the
// download rather than leaving the black areas to be discovered afterwards
const jpgExportHint =
  'Export a JPG of this data product. Areas with no data appear black.';

export default function DataProductDownloadMenu({
  dataProduct,
  projectId,
  setStatus,
}: {
  dataProduct: DataProduct;
  projectId: string | undefined;
  setStatus: React.Dispatch<React.SetStateAction<Status | null>>;
}) {
  const [isExporting, setIsExporting] = useState(false);

  const exportToJpeg = async () => {
    // Reported rather than ignored: without a project there is no URL to call,
    // and a menu item that does nothing at all looks like a broken download
    if (!projectId) {
      setStatus({
        type: 'error',
        msg: 'Unable to export image. Please try again.',
      });
      return;
    }

    setIsExporting(true);
    setStatus(null);

    try {
      await exportDataProductToJpeg(dataProduct, projectId);
    } catch (err) {
      console.error(err);
      setStatus({
        type: 'error',
        msg: 'Unable to export image. Please try again.',
      });
    } finally {
      setIsExporting(false);
    }
  };

  // Point clouds, panoramics, and 3DGS have no second format to choose from, so
  // they keep a plain download link instead of a menu
  if (!isGeoTIFF(dataProduct.data_type)) {
    return (
      <a
        href={dataProduct.url}
        target="_blank"
        download={dataProduct.download_filename ?? ''}
      >
        <ArrowDownTrayIcon
          className="w-5 h-5 hover:scale-110"
          title="Download data product"
        />
      </a>
    );
  }

  return (
    <Menu>
      <MenuButton
        type="button"
        disabled={isExporting}
        aria-label="Download data product"
        title="Download data product"
        className="flex items-center"
      >
        <ArrowDownTrayIcon
          className={clsx(
            'w-5 h-5',
            isExporting ? 'opacity-50' : 'hover:scale-110'
          )}
          aria-hidden="true"
        />
        <ChevronDownIcon className="h-3 w-3" aria-hidden="true" />
      </MenuButton>
      {/* anchor positions the panel in a portal, so it escapes the card's
          overflow-hidden wrapper and the card grid's overflow-y-auto */}
      <MenuItems
        anchor={{ to: 'bottom end', gap: 8 }}
        className="z-[70] w-48 rounded-md bg-white py-1 shadow-lg ring-1 ring-black/5 focus:outline-hidden"
      >
        <MenuItem>
          {({ focus }) => (
            <a
              className={clsx(menuItemClasses, focus && 'bg-gray-100')}
              href={dataProduct.url}
              target="_blank"
              download={dataProduct.download_filename ?? ''}
            >
              GeoTIFF (.tif)
            </a>
          )}
        </MenuItem>
        <MenuItem>
          {({ focus }) => (
            <button
              type="button"
              className={clsx(menuItemClasses, focus && 'bg-gray-100')}
              onClick={exportToJpeg}
              title={jpgExportHint}
            >
              Image (.jpg)
            </button>
          )}
        </MenuItem>
      </MenuItems>
    </Menu>
  );
}

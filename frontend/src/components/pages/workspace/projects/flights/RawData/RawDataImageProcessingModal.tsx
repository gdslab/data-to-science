import { useState } from 'react';
import { FaGears } from 'react-icons/fa6';
import Modal from '../../../../../Modal';
import MetashapeForm from './RawDataImageProcessingForm/MetashapeForm';
import ODMForm from './RawDataImageProcessingForm/ODMForm';
import {
  ImageProcessingBackend,
  MetashapeSettings,
  ODMSettings,
} from './RawData.types';
import { classNames } from '../../../../../utils';

type RawDataImageProcessingModal = {
  imageProcessingExts: ImageProcessingBackend[];
  isProcessing: boolean;
  onSubmitJob: (settings: MetashapeSettings | ODMSettings) => void;
};

export default function RawDataImageProcessingModal({
  imageProcessingExts,
  isProcessing,
  onSubmitJob,
}: RawDataImageProcessingModal) {
  const [open, setOpen] = useState(false);
  const [backend, setBackend] = useState<ImageProcessingBackend>(
    imageProcessingExts[0]
  );

  const toggleModal = () => setOpen(!open);

  return (
    <div>
      {/* box metrics match OutlineButton size="sm" so the pair aligns */}
      <button
        className="w-full text-sm font-bold py-2 px-4 border-2 border-accent2/90 rounded-md bg-accent2/90 text-white enabled:hover:bg-accent2 enabled:hover:border-accent2 disabled:opacity-75 disabled:cursor-not-allowed ease-in-out duration-300"
        type="button"
        name="processRawDataBtn"
        disabled={isProcessing}
        title="Generate DEM, orthomosaic, and point cloud data products from zipped raw data"
        onClick={() => setOpen(true)}
      >
        <span className="flex items-center justify-center gap-1.5">
          <FaGears className="w-3.5 h-3.5" />
          {isProcessing ? 'Processing' : 'Process'}
        </span>
      </button>
      <Modal open={open} setOpen={setOpen}>
        {imageProcessingExts.length > 1 && (
          <div className="flex gap-2 px-4 pt-4">
            {imageProcessingExts.map((ext) => (
              <button
                key={ext}
                className={classNames(
                  backend === ext
                    ? 'bg-accent2/90 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300',
                  'px-3 py-1 rounded-sm text-sm font-semibold'
                )}
                type="button"
                onClick={() => setBackend(ext)}
              >
                {ext === 'metashape' ? 'Metashape' : 'ODM'}
              </button>
            ))}
          </div>
        )}
        {backend === 'metashape' ? (
          <MetashapeForm onSubmitJob={onSubmitJob} toggleModal={toggleModal} />
        ) : (
          <ODMForm onSubmitJob={onSubmitJob} toggleModal={toggleModal} />
        )}
      </Modal>
    </div>
  );
}

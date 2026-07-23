import { useState } from 'react';
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
      <button
        className="w-32 bg-accent2/90 text-white font-semibold py-1 rounded-sm enabled:hover:bg-accent2 disabled:opacity-75 disabled:cursor-not-allowed"
        type="button"
        name="processRawDataBtn"
        disabled={isProcessing}
        title="Generate DEM, orthomosaic, and point cloud data products from zipped raw data"
        onClick={() => setOpen(true)}
      >
        {isProcessing ? 'Processing' : 'Process'}
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

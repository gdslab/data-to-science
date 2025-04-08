import { useState } from 'react';
import Modal from '../../../../Modal';
import MetashapeForm from './RawDataImageProcessingForm/MetashapeForm';
import ODMForm from './RawDataImageProcessingForm/ODMForm';
import { MetashapeSettings, ODMSettings } from './RawData.types';

type RawDataImageProcessingModal = {
  imageProcessingExt: 'metashape' | 'odm';
  isProcessing: boolean;
  onSubmitJob: (settings: MetashapeSettings | ODMSettings) => void;
};

export default function RawDataImageProcessingModal({
  imageProcessingExt,
  isProcessing,
  onSubmitJob,
}: RawDataImageProcessingModal) {
  const [open, setOpen] = useState(false);

  const toggleModal = () => setOpen(!open);

  return (
    <div>
      <button
        className="w-32 bg-accent2/90 text-white font-semibold py-1 rounded enabled:hover:bg-accent2 disabled:opacity-75 disabled:cursor-not-allowed"
        type="button"
        name="processRawDataBtn"
        disabled={isProcessing}
        title="Generate DEM, orthomosaic, and point cloud data products from zipped raw data"
        onClick={() => setOpen(true)}
      >
        {isProcessing ? 'Processing' : 'Process'}
      </button>
      <Modal open={open} setOpen={setOpen}>
        {imageProcessingExt === 'metashape' ? (
          <MetashapeForm onSubmitJob={onSubmitJob} toggleModal={toggleModal} />
        ) : (
          <ODMForm onSubmitJob={onSubmitJob} toggleModal={toggleModal} />
        )}
      </Modal>
    </div>
  );
}

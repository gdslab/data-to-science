import { useState } from 'react';
import Modal from '../../../../../Modal';
import RawDataImageProcessingForm from './RawDataImageProcessingForm';
import { ImageProcessingSettings } from './RawData.types';

type RawDataImageProcessingModal = {
  isProcessing: boolean;
  onSubmitJob: (settings: ImageProcessingSettings) => void;
};

export default function RawDataImageProcessingModal({
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
        <RawDataImageProcessingForm
          onSubmitJob={onSubmitJob}
          toggleModal={toggleModal}
        />
      </Modal>
    </div>
  );
}

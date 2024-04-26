import { Fragment, useEffect, useRef, useState } from 'react';
import { Dialog, Transition } from '@headlessui/react';

import DataProductUpload from './DataProductUpload';
import DataTypeRadioInput, { getAllowedFileTypes } from './DataTypeRadioInput';

interface Props {
  flightID: string;
  projectID: string;
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
}

export default function DataProductUploadModal({
  flightID,
  projectID,
  open,
  setOpen,
}: Props) {
  const cancelButtonRef = useRef(null);
  const [dtype, setDtype] = useState('dsm');
  const [dtypeOther, setDtypeOther] = useState('');
  const [dtypeOtherTouched, setDtypeOtherTouched] = useState(false);
  const [uploadHistory, setUploadHistory] = useState<string[]>([]);

  let uploadType: string | undefined = undefined;

  useEffect(() => {
    setDtype('dsm');
    setDtypeOther('');
    setDtypeOtherTouched(false);
    setUploadHistory([]);
  }, [open]);

  useEffect(() => {
    if (dtype !== 'other') {
      setDtypeOther('');
      setDtypeOtherTouched(false);
    }
  }, [dtype]);

  function updateUploadHistory(newUpload: string) {
    const currentUploadHistory = uploadHistory.slice();
    currentUploadHistory.push(newUpload);
    setUploadHistory(currentUploadHistory);
  }

  if (['dsm', 'ortho', 'point_cloud', 'other'].indexOf(dtype) > -1) {
    uploadType = 'dataProduct';
  } else if (dtype === 'raw') {
    uploadType = 'zip';
  } else {
    throw new Error('unknown data type');
  }

  return (
    <Transition.Root appear show={open} as={Fragment}>
      <Dialog
        as="div"
        className="relative z-10"
        initialFocus={cancelButtonRef}
        onClose={() => null}
      >
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />
        </Transition.Child>

        <div className="fixed inset-0 z-10 overflow-y-auto">
          <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
              enterTo="opacity-100 translate-y-0 sm:scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 translate-y-0 sm:scale-100"
              leaveTo="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
            >
              <Dialog.Panel className="relative transform overflow-hidden rounded-lg bg-white text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg">
                {uploadType === 'dataProduct' || uploadType === 'zip' ? (
                  <DataTypeRadioInput
                    dtype={dtype}
                    dtypeOther={dtypeOther}
                    setDtype={setDtype}
                    setDtypeOther={setDtypeOther}
                    setDtypeOtherTouched={setDtypeOtherTouched}
                  />
                ) : null}

                {dtype !== 'other' || (dtype === 'other' && dtypeOther.length > 1) ? (
                  <div className="bg-white px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                    <DataProductUpload
                      info={{
                        dtype: dtype,
                        endpoint: '/files',
                        flightID: flightID,
                        projectID: projectID,
                      }}
                      fileType={getAllowedFileTypes(dtype)}
                      uploadType={uploadType}
                      updateUploadHistory={updateUploadHistory}
                    />
                  </div>
                ) : dtypeOtherTouched ? (
                  <span className="px-4 pb-4 pt-5 sm:p-6 sm:pb-4 text-red-600">
                    Data type must be at least 2 characters in length
                  </span>
                ) : null}

                {uploadHistory.length > 0 ? (
                  <fieldset className="border border-solid border-slate-300 m-4 px-4 py-3 sm:px-6">
                    <legend className="block text-sm text-gray-400 font-bold pt-2 pb-1">
                      Previously uploaded:
                    </legend>
                    <ul className="list-disc max-h-32 overflow-y-auto">
                      {uploadHistory.map((recentUpload, index) => (
                        <li key={`upload-${index}`}>{recentUpload}</li>
                      ))}
                    </ul>
                  </fieldset>
                ) : null}

                <div className="flex items-center justify-between bg-gray-50 px-4 py-3 sm:px-6">
                  <span>
                    Click <strong>Done</strong> when you have finished uploading files.
                  </span>
                  <button
                    ref={cancelButtonRef}
                    type="button"
                    className="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto"
                    aria-label="Done button"
                    onClick={() => setOpen(false)}
                  >
                    Done
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition.Root>
  );
}

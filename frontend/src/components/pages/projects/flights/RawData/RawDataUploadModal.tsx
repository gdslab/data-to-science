import { Fragment, useEffect, useRef, useState } from 'react';
import { Dialog, DialogPanel, Transition, TransitionChild } from '@headlessui/react';

import DataProductUpload from '../DataProducts/DataProductUpload';

interface Props {
  flightID: string;
  projectID: string;
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
}

export default function RawDataUploadModal({
  flightID,
  projectID,
  open,
  setOpen,
}: Props) {
  const cancelButtonRef = useRef(null);
  const [uploadHistory, setUploadHistory] = useState<string[]>([]);

  useEffect(() => {
    setUploadHistory([]);
  }, [open]);

  function updateUploadHistory(newUpload: string) {
    const currentUploadHistory = uploadHistory.slice();
    currentUploadHistory.push(newUpload);
    setUploadHistory(currentUploadHistory);
  }

  return (
    <Transition appear show={open} as={Fragment}>
      <Dialog
        as="div"
        className="relative z-10"
        initialFocus={cancelButtonRef}
        onClose={() => null}
      >
        <TransitionChild
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />
        </TransitionChild>

        <div className="fixed inset-0 z-10 overflow-y-auto">
          <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
            <TransitionChild
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
              enterTo="opacity-100 translate-y-0 sm:scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 translate-y-0 sm:scale-100"
              leaveTo="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
            >
              <DialogPanel className="relative transform overflow-hidden rounded-lg bg-white text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg">
                <div className="bg-white px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                  <DataProductUpload
                    info={{
                      dtype: 'raw',
                      endpoint: '/files',
                      flightID: flightID,
                      projectID: projectID,
                    }}
                    fileType={['application/zip', 'application/x-zip-compressed']}
                    uploadType="rawData"
                    updateSetDisabled={() => {}}
                    updateUploadHistory={updateUploadHistory}
                  />
                </div>
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
              </DialogPanel>
            </TransitionChild>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}

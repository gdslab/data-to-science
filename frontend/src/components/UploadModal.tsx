import { Fragment, useRef, useState } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import FileUpload from './FileUpload';

interface Props {
  apiRoute: string;
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  uploadType: string;
}

function DtypeRadioInput({
  dtype,
  setDtype,
}: {
  dtype: string;
  setDtype: React.Dispatch<React.SetStateAction<string>>;
}) {
  function changeDtype(e) {
    if (e.target.value) {
      setDtype(e.target.value);
    }
  }

  return (
    <div className="px-4 py-3 sm:flex sm:px-6">
      <fieldset className="w-full flex flex-wrap justify-around gap-3">
        <legend className="sr-only">Data type</legend>

        <div>
          <input
            type="radio"
            name="dtypeOption"
            value="dsm"
            id="dtypeDSM"
            className="peer hidden"
            checked={dtype === 'dsm'}
            onChange={changeDtype}
          />

          <label
            htmlFor="dtypeDSM"
            className="flex cursor-pointer items-center justify-center rounded-md border border-gray-100 bg-white px-3 py-2 text-gray-900 hover:border-gray-200 peer-checked:border-blue-500 peer-checked:bg-blue-500 peer-checked:text-white"
          >
            <p className="text-sm font-medium">DSM</p>
          </label>
        </div>

        <div>
          <input
            type="radio"
            name="dtypeOption"
            value="point_cloud"
            id="dtypePointCloud"
            className="peer hidden"
            checked={dtype === 'point_cloud'}
            onChange={changeDtype}
          />

          <label
            htmlFor="dtypePointCloud"
            className="flex cursor-pointer items-center justify-center rounded-md border border-gray-100 bg-white px-3 py-2 text-gray-900 hover:border-gray-200 peer-checked:border-blue-500 peer-checked:bg-blue-500 peer-checked:text-white"
          >
            <p className="text-sm font-medium">Point Cloud</p>
          </label>
        </div>

        <div>
          <input
            type="radio"
            name="dtypeOption"
            value="other"
            id="dtypeOther"
            className="peer hidden"
            checked={dtype === 'other'}
            onChange={changeDtype}
          />

          <label
            htmlFor="dtypeOther"
            className="flex cursor-pointer items-center justify-center rounded-md border border-gray-100 bg-white px-3 py-2 text-gray-900 hover:border-gray-200 peer-checked:border-blue-500 peer-checked:bg-blue-500 peer-checked:text-white"
          >
            <p className="text-sm font-medium">Other</p>
          </label>
        </div>

        <div>
          <input
            type="radio"
            name="dtypeOption"
            value="ortho"
            id="dtypeOrtho"
            className="peer hidden"
            checked={dtype === 'ortho'}
            onChange={changeDtype}
          />

          <label
            htmlFor="dtypeOrtho"
            className="flex cursor-pointer items-center justify-center rounded-md border border-gray-100 bg-white px-3 py-2 text-gray-900 hover:border-gray-200 peer-checked:border-blue-500 peer-checked:bg-blue-500 peer-checked:text-white"
          >
            <p className="text-sm font-medium">Ortho</p>
          </label>
        </div>
      </fieldset>
    </div>
  );
}

export default function UploadModal({ apiRoute, open, setOpen, uploadType }: Props) {
  const cancelButtonRef = useRef(null);
  const [dtype, setDtype] = useState('dsm');

  return (
    <Transition.Root show={open} as={Fragment}>
      <Dialog
        as="div"
        className="relative z-10"
        initialFocus={cancelButtonRef}
        onClose={setOpen}
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
                <div className="bg-white px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
                  <FileUpload
                    endpoint={uploadType === 'tif' ? apiRoute + `?dtype=${dtype}` : ''}
                    restrictions={{
                      allowedFileTypes: uploadType === 'zip' ? ['.zip'] : ['.tif'],
                      maxNumberOfFiles: 1,
                      minNumberOfFiles: 1,
                    }}
                    uploadType={uploadType}
                  />
                </div>

                {uploadType === 'tif' ? (
                  <DtypeRadioInput dtype={dtype} setDtype={setDtype} />
                ) : null}

                <div className="bg-gray-50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
                  <button
                    type="button"
                    className="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto"
                    onClick={() => setOpen(false)}
                    ref={cancelButtonRef}
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

import { ChangeEvent } from 'react';

import { Status } from '../../../../Alert';

import uploadPageIcon from '../../../../../assets/upload-page-icon.svg';

export default function MapLayerFileInput({
  inputKey,
  uploadFile,
  setStatus,
  setUploadFile,
}: {
  inputKey: number;
  uploadFile: File | null;
  setStatus: React.Dispatch<React.SetStateAction<Status | null>>;
  setUploadFile: React.Dispatch<React.SetStateAction<File | null>>;
}) {
  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setStatus(null);

    const files = event.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      setUploadFile(file);
    }
  }

  function dropHandler(event: React.DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setStatus(null);
    if (event.dataTransfer.items.length > 0) {
      for (let itemIdx = 0; itemIdx < event.dataTransfer.items.length; itemIdx++) {
        if (event.dataTransfer.items[itemIdx].kind === 'file') {
          const file = event.dataTransfer.items[itemIdx].getAsFile();
          if (file) {
            setUploadFile(file);
          } else {
            setStatus({ type: 'error', msg: 'Unable to process file' });
          }
        } else {
          setStatus({ type: 'error', msg: 'Must be file' });
        }
      }
    } else {
      setStatus({ type: 'warning', msg: 'Must add file to get started' });
    }
  }

  function dragOverHandler(event: React.DragEvent<HTMLDivElement>) {
    event.preventDefault();
    if (event.dataTransfer.items.length > 1) {
      event.stopPropagation();
      setStatus({
        type: 'error',
        msg: 'Cannot upload more than a single file at a time.',
      });
    }
  }

  function dragLeaveHandler(event: React.DragEvent<HTMLDivElement>) {
    event.preventDefault();
  }

  return (
    <div
      className="w-96 h-64 flex flex-col items-center justify-center gap-4 rounded-lg bg-gray-50 border-dashed border-2 border-gray-400"
      onDrop={(event) => {
        // clear any form errors before processing new file
        dropHandler(event);
      }}
      onDragOver={dragOverHandler}
      onDragLeave={dragLeaveHandler}
    >
      <img src={uploadPageIcon} className="h-20" alt="Selected upload document" />
      {!uploadFile && <span className="text-gray-400">No file selected.</span>}
      {uploadFile && <span className="text-gray-600">{uploadFile.name}</span>}
      <label
        htmlFor="uploadMapLayer"
        className="px-4 py-2 text-white font-semibold rounded-md bg-blue-500/90 hover:bg-blue-500 cursor-pointer"
      >
        Browse
      </label>
      <input
        className="hidden"
        key={inputKey.toString()}
        type="file"
        id="uploadMapLayer"
        name="uploadMapLayer"
        accept="application/geo+json,application/json,application/zip"
        multiple={false}
        onChange={(event) => {
          // clear any form errors before processing new file
          handleFileChange(event);
        }}
      />
    </div>
  );
}

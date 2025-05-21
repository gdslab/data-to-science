import clsx from 'clsx';

export function getAllowedFileTypes(dtype: string): string[] {
  if (dtype === 'dem' || dtype === 'ortho' || dtype === 'other') {
    return ['.tif'];
  } else if (dtype === 'point_cloud') {
    return ['.las', '.laz'];
  } else {
    return ['.tif'];
  }
}

export default function DataTypeRadioInput({
  disabled,
  dtype,
  dtypeOther,
  setDtype,
  setDtypeOther,
  setDtypeOtherTouched,
}: {
  disabled: boolean;
  dtype: string;
  dtypeOther: string;
  setDtype: React.Dispatch<React.SetStateAction<string>>;
  setDtypeOther: React.Dispatch<React.SetStateAction<string>>;
  setDtypeOtherTouched: React.Dispatch<React.SetStateAction<boolean>>;
}) {
  function changeDtype(e) {
    if (e.target.value) {
      setDtype(e.target.value);
    }
  }

  function updateDtypeOther(e) {
    e.preventDefault();
    setDtypeOther(e.target.value);
  }

  return (
    <div className="px-4 py-3 flex flex-col gap-4 sm:px-6">
      <fieldset className="w-full flex flex-col border border-solid border-slate-300 p-1.5 gap-1.5">
        <legend className="block text-sm text-gray-400 font-bold pt-2 pb-1">
          Upload Data Type
        </legend>
        <div className="w-full flex justify-between">
          <div>
            <input
              type="radio"
              name="dtypeOption"
              value="dem"
              id="dtypeDEM"
              className="peer hidden"
              checked={dtype === 'dem'}
              onChange={changeDtype}
              disabled={disabled}
            />

            <label
              htmlFor="dtypeDEM"
              className={clsx(
                'flex items-center justify-center rounded-md border border-gray-100 bg-white px-3 py-2 text-gray-900 hover:border-gray-200 peer-checked:border-accent3 peer-checked:bg-accent3 peer-checked:text-white',
                {
                  'bg-gray-500 opacity-50 cursor-not-allowed': disabled,
                  'cursor-pointer': !disabled,
                }
              )}
            >
              <p className="text-sm font-medium">DEM</p>
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
              disabled={disabled}
            />

            <label
              htmlFor="dtypePointCloud"
              className={clsx(
                'flex items-center justify-center rounded-md border border-gray-100 bg-white px-3 py-2 text-gray-900 hover:border-gray-200 peer-checked:border-accent3 peer-checked:bg-accent3 peer-checked:text-white',
                {
                  'bg-gray-500 opacity-50 cursor-not-allowed': disabled,
                  'cursor-pointer': !disabled,
                }
              )}
            >
              <p className="text-sm font-medium">Point Cloud</p>
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
              disabled={disabled}
            />

            <label
              htmlFor="dtypeOrtho"
              className={clsx(
                'flex items-center justify-center rounded-md border border-gray-100 bg-white px-3 py-2 text-gray-900 hover:border-gray-200 peer-checked:border-accent3 peer-checked:bg-accent3 peer-checked:text-white',
                {
                  'bg-gray-500 opacity-50 cursor-not-allowed': disabled,
                  'cursor-pointer': !disabled,
                }
              )}
            >
              <p className="text-sm font-medium">Ortho</p>
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
              disabled={disabled}
            />

            <label
              htmlFor="dtypeOther"
              className={clsx(
                'flex items-center justify-center rounded-md border border-gray-100 bg-white px-3 py-2 text-gray-900 hover:border-gray-200 peer-checked:border-accent3 peer-checked:bg-accent3 peer-checked:text-white',
                {
                  'bg-gray-500 opacity-50 cursor-not-allowed': disabled,
                  'cursor-pointer': !disabled,
                }
              )}
            >
              <p className="text-sm font-medium">Other</p>
            </label>
          </div>
        </div>
        {dtype === 'other' ? (
          <fieldset className="w-full flex flex-wrap justify-evenly gap-1.5">
            <legend className="sr-only">Data type other</legend>
            <label htmlFor="Search" className="sr-only">
              Other
            </label>
            <input
              type="text"
              id="dTypeOther"
              placeholder="Enter other data type (e.g., NDVI)"
              className="w-full rounded-md border-gray-200 px-4 py-2.5 pe-10 shadow sm:text-sm"
              value={dtypeOther}
              onChange={updateDtypeOther}
              onBlur={() => setDtypeOtherTouched(true)}
              disabled={disabled}
            />
          </fieldset>
        ) : null}
        <span>
          Accepted file extensions:{' '}
          <strong>{getAllowedFileTypes(dtype).join(' ')}</strong>
        </span>
      </fieldset>
    </div>
  );
}

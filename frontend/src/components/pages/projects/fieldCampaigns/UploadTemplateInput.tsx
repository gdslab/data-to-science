import { useFormikContext } from 'formik';
import Papa from 'papaparse';
import { useState } from 'react';

export interface TemplateInput {
  [key: string]: unknown;
}

/**
 * Compares two arrays of header names. Returns true if both arrays
 * are the same size and contain same header names in same order.
 * @param {string[]} headers1 First array of header names.
 * @param {string[]} headers2 Second array of header names.
 * @returns {boolean} True if both arrays match, false otherwise.
 */
const headersMatch = (headers1: string[], headers2: string[]): boolean => {
  if (headers1.length !== headers2.length) return false;
  for (let i = 0; i < headers1.length; i++) {
    if (headers1[i] !== headers2[i]) return false;
  }
  return true;
};

export default function UploadTemplateInput({
  setCSVData,
  toggleShowTemplateOptions,
}: {
  setCSVData: React.Dispatch<React.SetStateAction<TemplateInput[]>>;
  toggleShowTemplateOptions: React.Dispatch<React.SetStateAction<boolean>>;
}) {
  const [csvParseErrors, setCSVParseErrors] = useState<
    Papa.ParseError[] | Omit<Papa.ParseError, 'code'>[]
  >([]);
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const { setFieldValue, setFieldTouched } = useFormikContext();

  return (
    <div className="flex flex-col gap-2">
      <label
        className="block text-sm text-slate-600 font-semibold pb-1"
        htmlFor="uploadInput"
      >
        Upload input (Multiple .csv files allowed)
      </label>
      <input
        id="uploadInput"
        type="file"
        accept=".csv"
        multiple
        onChange={(event) => {
          setCSVData([]);
          setCSVParseErrors([]);
          setSelectedFiles([]);
          if (
            event.currentTarget &&
            event.currentTarget.files &&
            event.currentTarget.files.length > 0
          ) {
            const uploadedFiles = [...event.currentTarget.files];
            // create array of promises for each file's parse results
            Promise.all<Papa.ParseResult<TemplateInput>>(
              uploadedFiles.map(
                (file) =>
                  new Promise((resolve, _reject) =>
                    Papa.parse(file, {
                      header: true,
                      dynamicTyping: true,
                      complete: (results: Papa.ParseResult<TemplateInput>) =>
                        resolve(results),
                    })
                  )
              )
            ).then((results) => {
              // track previous headers to make comparisons between files
              let prevHeaders: string[] | undefined = undefined;
              // store parse results from all files
              const allCSVData: TemplateInput[] = [];
              // store names of parsed files
              const parsedFiles: string[] = [];
              // iterate over each file
              results.forEach((result, index) => {
                // check for errors
                if (result.errors.length > 0) {
                  setCSVParseErrors(result.errors);
                  throw new Error(`Error occurred in ${uploadedFiles[index].name}`);
                } else {
                  // add headers (if any) to template input field array
                  if (result.meta.fields && result.meta.fields.length > 0) {
                    if (!prevHeaders) {
                      prevHeaders = result.meta.fields;
                    } else {
                      // verify header length and names match between files
                      if (!headersMatch(prevHeaders, result.meta.fields)) {
                        setFieldValue('templateInput', []);
                        setCSVParseErrors([
                          {
                            message: `Headers do not match in ${uploadedFiles[index].name}`,
                          } as Omit<Papa.ParseError, 'code'>,
                        ]);
                        throw new Error(
                          `Error occurred in ${uploadedFiles[index].name}`
                        );
                      }
                    }
                    // add header values to form
                    setFieldValue('templateInput', result.meta.fields);
                    result.meta.fields.forEach((_val, index) => {
                      setFieldTouched(`templateInput.${index}`, true);
                    });
                    // store csv data
                    allCSVData.push(...result.data);
                    // show next step
                    toggleShowTemplateOptions(true);
                    // add file to list
                    parsedFiles.push(uploadedFiles[index].name);
                  } else {
                    setCSVParseErrors([
                      { message: 'Unable to detect headers' } as Omit<
                        Papa.ParseError,
                        'code'
                      >,
                    ]);
                    throw new Error(`Error occurred in ${uploadedFiles[index].name}`);
                  }
                }
                setCSVData(allCSVData);
                setSelectedFiles(parsedFiles);
              });
            });
          }
        }}
      />
      {selectedFiles.length > 0 ? (
        <div>
          <span className="block text-sm text-slate-600 font-semibold pb-1">
            Selected Files:
          </span>
          <ul className="list-disc list-inside">
            {selectedFiles.map((filename: string, index: number) => (
              <li key={index}>{filename}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {csvParseErrors.length > 0 ? (
        <ul className="list-disc list-inside text-red-500">
          {csvParseErrors.map(
            (err: Papa.ParseError | Omit<Papa.ParseError, 'code'>, index: number) => (
              <li key={index}>{`${'code' in err ? err.code : 'Unknown'}${
                err.row ? ` (Row ${err.row})` : ''
              }: ${err.message}`}</li>
            )
          )}
        </ul>
      ) : null}
    </div>
  );
}

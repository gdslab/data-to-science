import Papa from 'papaparse';
import { useState } from 'react';
import Uppy from '@uppy/core';
import { DragDrop } from '@uppy/react';
import FileInput from '@uppy/file-input';

import '@uppy/core/dist/style.min.css';
import '@uppy/drag-drop/dist/style.min.css';
import { useFormikContext } from 'formik';

import { TemplateInput, TemplateUpload } from './FieldCampaign';

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

export default function UppyTemplateUpload({ id, updateCsvErrors }: TemplateUpload) {
  const [uppy] = useState(() => new Uppy().use(FileInput, { id: id }));

  const { setFieldValue, setFieldTouched } = useFormikContext();

  uppy.on('files-added', (files) => {
    // remove any previously tracked errors
    updateCsvErrors([], id, 'clear');
    // add filename(s) to formik context
    const filenames = files.map(({ meta }) => meta.name);
    setFieldValue(`treatments.${id}.filenames`, filenames);
    setFieldTouched(`treatments.${id}.filenames`, true);
    // create array of promises for each file's parse results
    Promise.all<Papa.ParseResult<TemplateInput>>(
      files.map(
        (file) =>
          new Promise((resolve, _reject) =>
            Papa.parse(file.data as File, {
              header: true,
              dynamicTyping: true,
              skipEmptyLines: true,
              complete: (results: Papa.ParseResult<TemplateInput>) => resolve(results),
            })
          )
      )
    ).then((results) => {
      // add file headers to formik context
      if (results[0].meta.fields && results[0].meta.fields.length > 0) {
        results[0].meta.fields.forEach((headerName, headerIndex) => {
          setFieldValue(`treatments.${id}.columns.${headerIndex}`, {
            name: headerName,
            selected: true,
          });
          setFieldTouched(`treatments.${id}.columns.${headerIndex}.name`, true);
          setFieldTouched(`treatments.${id}.columns.${headerIndex}.selected`, true);
        });
      }
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
          updateCsvErrors(result.errors, id, 'add');
          setFieldValue(`treatments.${id}.columns`, []);
          throw new Error(`Error occurred in ${files[index].name}`);
        } else {
          // add headers (if any) to template input field array
          if (result.meta.fields && result.meta.fields.length > 0) {
            if (!prevHeaders) {
              prevHeaders = result.meta.fields;
            } else {
              // verify header length and names match between files
              if (!headersMatch(prevHeaders, result.meta.fields)) {
                updateCsvErrors(
                  [
                    {
                      message: `Headers do not match in ${files[index].name}`,
                    } as Omit<Papa.ParseError, 'code'>,
                  ],
                  id,
                  'add'
                );
                setFieldValue(`treatments.${id}.columns`, []);
                throw new Error(`Error occurred in ${files[index].name}`);
              }
            }
            // add header values to form
            setFieldValue('templateInput', result.meta.fields);
            result.meta.fields.forEach((_val, index) => {
              setFieldTouched(`templateInput.${index}`, true);
            });
            // store csv data
            allCSVData.push(...result.data);
            // add file to list
            parsedFiles.push(files[index].name || 'unknown');
          } else {
            updateCsvErrors(
              [
                { message: 'Unable to detect headers' } as Omit<
                  Papa.ParseError,
                  'code'
                >,
              ],
              id,
              'add'
            );
            setFieldValue(`treatments.${id}.columns`, []);
            throw new Error(`Error occurred in ${files[index].name}`);
          }
        }
        setFieldValue(`treatments.${id}.data`, allCSVData);
        setFieldTouched(`treatments.${id}.data`, true);
      });
    });
  });

  return <DragDrop uppy={uppy} />;
}

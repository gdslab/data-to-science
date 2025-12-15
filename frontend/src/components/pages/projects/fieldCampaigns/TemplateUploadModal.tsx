import Papa from 'papaparse';
import { useEffect, useMemo, useState } from 'react';
import Uppy from '@uppy/core';
import DashboardModal from '@uppy/react/dashboard-modal';
import '@uppy/core/css/style.min.css';
import '@uppy/dashboard/css/style.min.css';
import { useFormikContext } from 'formik';

import { TemplateInput, UpdateCSVErrors } from './FieldCampaign';
import { headersMatch } from './csvUploadUtils';

interface TemplateUploadModalProps {
  id: string;
  open: boolean;
  setOpen: (open: boolean) => void;
  updateCsvErrors: UpdateCSVErrors;
}

export default function TemplateUploadModal({
  id,
  open,
  setOpen,
  updateCsvErrors,
}: TemplateUploadModalProps) {
  const [uppy] = useState(() => new Uppy());
  const { setFieldValue, setFieldTouched } = useFormikContext();

  const restrictions = useMemo(
    () => ({
      allowedFileTypes: ['.csv'],
      minNumberOfFiles: 1,
    }),
    []
  );

  useEffect(() => {
    uppy.setOptions({ restrictions });
  }, [uppy, restrictions]);

  useEffect(() => {
    const handleRestrictionFailed = () => {
      uppy.info(
        {
          message: 'Unsupported file extension',
          details: `Upload must be CSV (.csv) files`,
        },
        'error',
        5000
      );
    };

    const handleFilesAdded = (files: Uppy.UppyFile[]) => {
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
                complete: (results: Papa.ParseResult<TemplateInput>) =>
                  resolve(results),
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
            setFieldTouched(
              `treatments.${id}.columns.${headerIndex}.selected`,
              true
            );
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
            uppy.info(
              {
                message: 'CSV parsing failed',
                details: `Error in ${files[index].name}`,
              },
              'error',
              10000
            );
            throw new Error(`Error occurred in ${files[index].name}`);
          } else {
            // add headers (if any) to template input field array
            if (result.meta.fields && result.meta.fields.length > 0) {
              if (!prevHeaders) {
                prevHeaders = result.meta.fields;
              } else {
                // verify header length and names match between files
                if (!headersMatch(prevHeaders, result.meta.fields)) {
                  const errorMessage = `Headers do not match in ${files[index].name}`;
                  updateCsvErrors(
                    [
                      {
                        message: errorMessage,
                      } as Omit<Papa.ParseError, 'code'>,
                    ],
                    id,
                    'add'
                  );
                  setFieldValue(`treatments.${id}.columns`, []);
                  uppy.info(
                    {
                      message: 'Header mismatch',
                      details: errorMessage,
                    },
                    'error',
                    10000
                  );
                  throw new Error(errorMessage);
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
              const errorMessage = 'Unable to detect headers';
              updateCsvErrors(
                [
                  { message: errorMessage } as Omit<
                    Papa.ParseError,
                    'code'
                  >,
                ],
                id,
                'add'
              );
              setFieldValue(`treatments.${id}.columns`, []);
              uppy.info(
                {
                  message: 'CSV parsing failed',
                  details: errorMessage,
                },
                'error',
                10000
              );
              throw new Error(errorMessage);
            }
          }
          setFieldValue(`treatments.${id}.data`, allCSVData);
          setFieldTouched(`treatments.${id}.data`, true);
        });

        // Success - close modal after short delay
        setTimeout(() => setOpen(false), 500);
      });
    };

    uppy.on('restriction-failed', handleRestrictionFailed);
    uppy.on('files-added', handleFilesAdded);

    return () => {
      uppy.off('restriction-failed', handleRestrictionFailed);
      uppy.off('files-added', handleFilesAdded);
    };
  }, [uppy, id, restrictions, updateCsvErrors, setFieldValue, setFieldTouched, setOpen]);

  return (
    <DashboardModal
      uppy={uppy}
      open={open}
      onRequestClose={() => setOpen(false)}
      closeAfterFinish={false}
      proudlyDisplayPoweredByUppy={false}
      disableThumbnailGenerator={true}
      locale={{
        strings: {
          dropPasteFiles: 'Drop CSV files here or %{browseFiles}',
        },
      }}
    />
  );
}

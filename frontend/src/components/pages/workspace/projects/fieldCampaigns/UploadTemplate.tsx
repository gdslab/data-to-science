import { useFormikContext } from 'formik';
import { useState } from 'react';
import YAML from 'yaml';

import { addToConfigForm, validateConfigYAML, YAMLConfig } from './utils';

export default function UploadTemplate({
  toggleShowConfigForm,
}: {
  toggleShowConfigForm: React.Dispatch<React.SetStateAction<boolean>>;
}) {
  const [ymlParseErrors, setYmlParseErrors] = useState<string[]>([]);
  const { setFieldValue, setFieldTouched } = useFormikContext();

  return (
    <div className="flex flex-col">
      <h4>Load previous template (.yml)</h4>
      <div className="flex flex-col gap-1.5">
        <label
          className="block text-sm text-slate-600 font-semibold pb-1"
          htmlFor="uploadTemplate"
        >
          Upload template
        </label>
        <input
          id="uploadTemplate"
          type="file"
          onChange={(event) => {
            if (
              event.currentTarget &&
              event.currentTarget.files &&
              event.currentTarget.files.length > 0
            ) {
              const uploadedFile = event.currentTarget.files[0];
              const reader = new FileReader();
              reader.onload = (event) => {
                if (event.target) {
                  const content = event.target.result;
                  if (typeof content === 'string') {
                    const data: YAMLConfig = YAML.parse(content);
                    const errors = validateConfigYAML(data);
                    if (errors.length > 0) {
                      setYmlParseErrors(errors);
                    } else {
                      addToConfigForm(data, {
                        setFieldValue,
                        setFieldTouched,
                      });
                      toggleShowConfigForm(true);
                    }
                  }
                }
              };
              reader.readAsText(uploadedFile);
            }
          }}
        />
        {ymlParseErrors.length > 0 ? (
          <ul className="list-disc list-inside text-red-500">
            {ymlParseErrors.map((err, index) => (
              <li key={index}>{err}</li>
            ))}
          </ul>
        ) : null}
      </div>
    </div>
  );
}

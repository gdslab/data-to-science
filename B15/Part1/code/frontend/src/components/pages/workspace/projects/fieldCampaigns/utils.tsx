import { FormikHelpers, FormikValues } from 'formik';

import { ProjectMember } from '../ProjectAccess';

/**
 * Finds user in array of project members and constructs full name string.
 * @param leadId User ID for project member.
 * @param projectMembers Array of project member objects.
 * @returns String of user's full name or 'unknown' if no matching user found.
 */
export function getFullName(
  leadId: string,
  projectMembers: ProjectMember[] | null
): string {
  if (!projectMembers) return 'Unknown';
  const leadUser = projectMembers.filter(({ member_id }) => member_id === leadId);
  if (leadUser.length > 0) return leadUser[0].full_name;
  return 'Unknown';
}

export interface YAMLConfig {
  TEMPLATE_INPUT: string[];
  COLUMNS_TEMPLATE: string[];
  NEW_COLUMNS: { [key: string]: string }[];
  SAMPLES_PER_PLOT: {
    Sample_name: string[];
  };
  SAMPLE_IDENTIFIER: {
    id_observation: string[];
  };
  TEMPLATE_OUTPUT: string[];
}

function addToConfigForm(
  yamlConfig: YAMLConfig,
  helpers: Partial<FormikHelpers<FormikValues>>
) {
  const { setFieldValue, setFieldTouched } = helpers;
  if (!setFieldValue || !setFieldTouched) {
    throw new Error('Missing formik helpers');
  }

  if (yamlConfig.NEW_COLUMNS) {
    setFieldValue(
      'newColumns',
      Object.keys(yamlConfig.NEW_COLUMNS).map((key) => ({
        name: key,
        fill: yamlConfig.NEW_COLUMNS[key],
      }))
    );
    Object.keys(yamlConfig.NEW_COLUMNS).forEach((_val, index) => {
      setFieldTouched(`newColumns.${index}`, true);
    });
  }
  if (yamlConfig.SAMPLES_PER_PLOT && yamlConfig.SAMPLES_PER_PLOT.Sample_name) {
    setFieldValue('sampleNames', yamlConfig.SAMPLES_PER_PLOT.Sample_name);
    yamlConfig.SAMPLES_PER_PLOT.Sample_name.forEach((_val, index) => {
      setFieldTouched(`sampleNames.${index}`, true);
    });
  }
  if (yamlConfig.SAMPLE_IDENTIFIER && yamlConfig.SAMPLE_IDENTIFIER.id_observation) {
    setFieldValue('sampleIdentifiers', yamlConfig.SAMPLE_IDENTIFIER.id_observation);
    yamlConfig.SAMPLE_IDENTIFIER.id_observation.forEach((_val, index) => {
      setFieldTouched(`sampleIdentifiers.${index}`, true);
    });
  }
  if (yamlConfig.TEMPLATE_OUTPUT) {
    setFieldValue('templateOutput', yamlConfig.TEMPLATE_OUTPUT);
    yamlConfig.TEMPLATE_OUTPUT.forEach((_val, index) => {
      setFieldTouched(`templateOutput.${index}`, true);
    });
  }
}

function validateConfigYAML(yamlConfig: YAMLConfig): string[] {
  const errors: string[] = [];
  if (!('TEMPLATE_INPUT' in yamlConfig))
    errors.push('Missing TEMPLATE_INPUT in yaml config');
  if (!('NEW_COLUMNS' in yamlConfig)) errors.push('Missing NEW_COLUMNS in yaml config');
  if (!('SAMPLES_PER_PLOT' in yamlConfig)) {
    errors.push('Missing SAMPLES_PER_PLOT in yaml config');
  } else {
    if (
      (yamlConfig.SAMPLES_PER_PLOT &&
        typeof yamlConfig.SAMPLES_PER_PLOT === 'object' &&
        !('Sample_name' in yamlConfig.SAMPLES_PER_PLOT)) ||
      !yamlConfig.SAMPLES_PER_PLOT
    ) {
      errors.push('Missing SAMPLES_PER_PLOT.Sample_name in yaml config');
    }
  }
  if (!('SAMPLE_IDENTIFIER' in yamlConfig)) {
    errors.push('Missing SAMPLE_IDENTIFIER in yaml config');
  } else {
    if (
      (yamlConfig.SAMPLE_IDENTIFIER &&
        typeof yamlConfig.SAMPLE_IDENTIFIER === 'object' &&
        !('id_observation' in yamlConfig.SAMPLE_IDENTIFIER)) ||
      !yamlConfig.SAMPLE_IDENTIFIER
    ) {
      errors.push('Missing SAMPLE_IDENTIFIERS.id_observation in yaml config');
    }
  }
  if (!('TEMPLATE_OUTPUT' in yamlConfig))
    errors.push('Missing TEMPLATE_OUTPUT in yaml config');
  return errors;
}

/**
 * Returns filename from Content-Disposition header or null if
 * no filename is matched.
 * @param contentDisposition Content-Disposition header from API response.
 * @returns Filename or null.
 */
function getFilenameFromContentDisposition(contentDisposition: string): string | null {
  if (!contentDisposition) return null;
  // match filename with optional double quotes encapsulating the filename
  const matches = contentDisposition.match(/filename="?([^";]+)"?/);
  if (matches && matches.length > 1) {
    return matches[1];
  }

  return null;
}

/**
 * Creates link element for file download, initiates file download, and
 * removes link element.
 * @param blob File to be downloaded.
 * @param downloadFilename Filename for download.
 */
function downloadFile(blob: Blob, downloadFilename: string): void {
  // create temp url for blob
  const downloadUrl = URL.createObjectURL(blob);
  // create temp link element for download
  const link = document.createElement('a');
  link.href = downloadUrl;
  // set filename from content-disposition as download filename
  link.setAttribute('download', downloadFilename);
  // add link to document body
  document.body.appendChild(link);
  // "click" link to initiate download
  link.click();
  // remove temp URL and link element
  URL.revokeObjectURL(downloadUrl);
  document.body.removeChild(link);
}

export {
  addToConfigForm,
  downloadFile,
  getFilenameFromContentDisposition,
  validateConfigYAML,
};

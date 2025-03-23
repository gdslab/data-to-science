import axios, { AxiosResponse, isAxiosError } from 'axios';
import { FormProvider, SubmitHandler, useForm } from 'react-hook-form';
import * as Yup from 'yup';
import { yupResolver } from '@hookform/resolvers/yup';

import { SelectField } from '../../../FormFields';
import { IndoorProjectDataVizAPIResponse } from './IndoorProject';

type CameraOrientation = 'top' | 'side';
type Filter2Options =
  | 'treatment'
  | 'description'
  | 'treatment_description'
  | 'all_pots'
  | 'single_pot';
type DateOptions = 'date' | 'dateAfterPlanting';

const cameraOrientationOptions: { label: string; value: CameraOrientation }[] =
  [
    { label: 'Top', value: 'top' },
    { label: 'Side', value: 'side' },
  ];
const filter2Options: { label: string; value: Filter2Options }[] = [
  { label: 'Treatment', value: 'treatment' },
  { label: 'Description', value: 'description' },
  { label: 'Treatment & Description', value: 'treatment_description' },
  { label: 'All Pots', value: 'all_pots' },
  { label: 'Single Pot', value: 'single_pot' },
];
// const dateOptions: { label: string; value: DateOptions }[] = [
//   { label: 'Date', value: 'date' },
//   { label: 'Date after planting', value: 'dateAfterPlanting' },
// ];

type VizFormData = {
  cameraOrientation: CameraOrientation;
  filter2: Filter2Options;
  date: DateOptions;
};

const defaultValues: VizFormData = {
  cameraOrientation: 'top',
  filter2: 'treatment',
  date: 'dateAfterPlanting',
};

const validationSchema = Yup.object({
  cameraOrientation: Yup.string()
    .oneOf(['top', 'side'], 'Invalid value')
    .required('Required field'),
  filter2: Yup.string()
    .oneOf(
      [
        'treatment',
        'description',
        'treatment_description',
        'all_pots',
        'single_pot',
      ],
      'Invalid value'
    )
    .required('Required field'),
  date: Yup.string()
    .oneOf(['date', 'dateAfterPlanting'], 'Invalid value')
    .required('Required field'),
});

export default function IndoorProjectDataVizForm({
  indoorProjectId,
  indoorProjectDataId,
  setIndoorProjectDataVizData,
}: {
  indoorProjectId: string;
  indoorProjectDataId: string | undefined;
  setIndoorProjectDataVizData: React.Dispatch<
    React.SetStateAction<IndoorProjectDataVizAPIResponse | null>
  >;
}) {
  const methods = useForm<VizFormData>({
    defaultValues,
    resolver: yupResolver(validationSchema),
  });

  const {
    formState: { isSubmitting },
    handleSubmit,
  } = methods;

  const onSubmit: SubmitHandler<VizFormData> = async (values) => {
    setIndoorProjectDataVizData(null);

    if (!indoorProjectDataId) return;

    try {
      const data = await fetchIndoorProjectVizData(
        indoorProjectId,
        indoorProjectDataId,
        values.cameraOrientation,
        values.filter2
      );
      setIndoorProjectDataVizData(data);
    } catch (error) {
      // Re-throw the error to be handled by the form's error handling
      throw error;
    }
  };

  return (
    <div className="my-2">
      <span className="block font-bold">Graph 1 Options</span>
      <FormProvider {...methods}>
        <form className="flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)}>
          <div className="flex items-start gap-8">
            {/* Camera Orientation */}
            <SelectField
              label="Camera Orientation"
              name="cameraOrientation"
              options={cameraOrientationOptions}
            />
            {/* Filter2 */}
            <SelectField
              label="Group pots by"
              name="filter2"
              options={filter2Options}
            />
            {/* Filter3 */}
            {/* <SelectField label="Date" name="date" options={dateOptions} /> */}
          </div>
          {/* Submit button */}
          <div className="w-48">
            <button
              type="submit"
              disabled={isSubmitting}
              className="max-h-12 px-4 py-2 bg-blue-500 text-white font-medium rounded hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-300 disabled:bg-blue-500/60 disabled:cursor-not-allowed"
            >
              {!isSubmitting ? 'Create Graph 1' : 'Generating graph 1...'}
            </button>
          </div>
        </form>
      </FormProvider>
    </div>
  );
}

export async function fetchIndoorProjectVizData(
  indoorProjectId: string,
  indoorProjectDataId: string,
  cameraOrientation: CameraOrientation,
  groupBy: Filter2Options
): Promise<IndoorProjectDataVizAPIResponse> {
  let endpoint = `${import.meta.env.VITE_API_V1_STR}/indoor_projects/`;
  endpoint += `${indoorProjectId}/uploaded/${indoorProjectDataId}/data_for_viz`;

  try {
    const queryParams = {
      camera_orientation: cameraOrientation,
      group_by: groupBy,
    };
    const results: AxiosResponse<IndoorProjectDataVizAPIResponse> =
      await axios.get(endpoint, { params: queryParams });
    return results.data;
  } catch (error) {
    if (isAxiosError(error)) {
      // Axios-specific error handling
      const status = error.response?.status || 500;
      const message = error.response?.data?.message || error.message;

      throw {
        status,
        message: `Failed to generate chart data: ${message}`,
      };
    } else {
      // Generic error handling
      throw {
        status: 500,
        message: 'An unexpected error occurred.',
      };
    }
  }
}

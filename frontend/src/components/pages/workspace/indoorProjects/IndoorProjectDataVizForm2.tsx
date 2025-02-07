import axios, { AxiosResponse, isAxiosError } from 'axios';
import {
  FormProvider,
  SubmitHandler,
  useForm,
  useWatch,
} from 'react-hook-form';
import * as Yup from 'yup';
import { yupResolver } from '@hookform/resolvers/yup';

import { SelectField } from '../../../FormFields';
import {
  IndoorProjectDataViz2APIResponse,
  NumericColumns,
} from './IndoorProject';

type CameraOrientation = 'top' | 'side';
type Filter2Options = 'treatment' | 'description' | 'both' | 'none';
type TargetTrait = string;
type DateSelection = 'date' | 'dateAfterPlanting';

const cameraOrientationOptions: { label: string; value: CameraOrientation }[] =
  [
    { label: 'Top', value: 'top' },
    { label: 'Side', value: 'side' },
  ];
const filter2Options: { label: string; value: Filter2Options }[] = [
  { label: 'Treatment', value: 'treatment' },
  { label: 'Description', value: 'description' },
  { label: 'Treatment & Description', value: 'both' },
  { label: 'None', value: 'none' },
];
// const dateSelectionOptions: { label: string; value: DateSelection }[] = [
//   { label: 'Date', value: 'date' },
//   { label: 'Date after planting', value: 'dateAfterPlanting' },
// ];

type VizFormData = {
  cameraOrientation: CameraOrientation;
  filter2: Filter2Options;
  targetTrait: TargetTrait;
  dateSelection: DateSelection;
};

const defaultValues: VizFormData = {
  cameraOrientation: 'top',
  filter2: 'treatment',
  targetTrait: '',
  dateSelection: 'dateAfterPlanting',
};

const validationSchema = Yup.object({
  cameraOrientation: Yup.string()
    .oneOf(['top', 'side'], 'Invalid value')
    .required('Required field'),
  filter2: Yup.string()
    .oneOf(['treatment', 'description', 'both', 'none'], 'Invalid value')
    .required('Required field'),
  targetTrait: Yup.string().required('Required field'),
  dateSelection: Yup.string()
    .oneOf(['date', 'dateAfterPlanting'], 'Invalid value')
    .required('Required field'),
});

export default function IndoorProjectDataViz2Form({
  indoorProjectId,
  indoorProjectDataId,
  numericColumns,
  setIndoorProjectDataViz2Data,
}: {
  indoorProjectId: string;
  indoorProjectDataId: string | undefined;
  numericColumns: NumericColumns;
  setIndoorProjectDataViz2Data: React.Dispatch<
    React.SetStateAction<IndoorProjectDataViz2APIResponse | null>
  >;
}) {
  const methods = useForm<VizFormData>({
    defaultValues,
    resolver: yupResolver(validationSchema),
  });

  const {
    control,
    formState: { isSubmitting },
    handleSubmit,
    // getValues,
  } = methods;

  const selectedCameraOrientation = useWatch({
    control,
    name: 'cameraOrientation',
  });

  const targetTraitOptions =
    selectedCameraOrientation === 'top'
      ? numericColumns.top.map((col) => ({ label: col, value: col }))
      : numericColumns.side.map((col) => ({ label: col, value: col }));

  const onSubmit: SubmitHandler<VizFormData> = async (values) => {
    setIndoorProjectDataViz2Data(null);

    if (!indoorProjectDataId) return;

    let endpoint = `${import.meta.env.VITE_API_V1_STR}/indoor_projects/`;
    endpoint += `${indoorProjectId}/uploaded/${indoorProjectDataId}/data_for_viz2`;

    try {
      const queryParams = {
        camera_orientation: values.cameraOrientation,
        group_by: values.filter2,
        trait: values.targetTrait,
      };
      const results: AxiosResponse<IndoorProjectDataViz2APIResponse> =
        await axios.get(endpoint, { params: queryParams });
      setIndoorProjectDataViz2Data(results.data);
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
  };

  return (
    <div className="my-2">
      <span className="block font-bold">Graph 2 Options</span>
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
              label="Filter 2"
              name="filter2"
              options={filter2Options}
            />
            {/* Target Trait */}
            <SelectField
              label="Target Trait"
              name="targetTrait"
              options={targetTraitOptions}
            />
            {/* Filter3 */}
            {/* <SelectField
            label="Date Selection"
            name="dateSelection"
            options={dateSelectionOptions}
          /> */}
          </div>
          {/* Submit button */}
          <div className="w-48">
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-blue-500 text-white font-medium rounded hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-300 disabled:bg-blue-500/60 disabled:cursor-not-allowed"
            >
              {!isSubmitting ? 'Create Graph 2' : 'Generating graph 2...'}
            </button>
          </div>
        </form>
      </FormProvider>
    </div>
  );
}

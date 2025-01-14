import { FormProvider, SubmitHandler, useForm } from 'react-hook-form';
import * as Yup from 'yup';
import { yupResolver } from '@hookform/resolvers/yup';
import { SelectField } from '../../../FormFields';

type Filter1Options = 'top' | 'side';
type Filter2Options = 'treatment' | 'description' | 'both' | 'none';

const filter1Options: { label: string; value: Filter1Options }[] = [
  { label: 'Top', value: 'top' },
  { label: 'Side', value: 'side' },
];
const filter2Options: { label: string; value: Filter2Options }[] = [
  { label: 'Treatment', value: 'treatment' },
  { label: 'Description', value: 'description' },
  { label: 'Treatment & Description', value: 'both' },
  { label: 'None', value: 'none' },
];

type VizFormData = {
  filter1: Filter1Options;
  filter2: Filter2Options;
};

const defaultValues: VizFormData = {
  filter1: 'top',
  filter2: 'treatment',
};

const validationSchema = Yup.object({
  filter1: Yup.string()
    .oneOf(['top', 'side'], 'Invalid value')
    .required('Required field'),
  filter2: Yup.string()
    .oneOf(['treatment', 'description', 'both', 'none'], 'Invalid value')
    .required('Required field'),
});

export default function IndoorProjectDataVizForm() {
  const methods = useForm<VizFormData>({
    defaultValues,
    resolver: yupResolver(validationSchema),
  });

  const {
    formState: { isSubmitting },
    handleSubmit,
  } = methods;

  const onSubmit: SubmitHandler<VizFormData> = async (values) => {
    console.log(values);
  };

  return (
    <div className="my-2">
      <span className="font-bold">Filter Options</span>
      <FormProvider {...methods}>
        <form onSubmit={handleSubmit(onSubmit)}>
          {/* Filter1 */}
          <SelectField label="Filter 1" name="filter1" options={filter1Options} />
          {/* Filter2 */}
          <SelectField label="Filter 2" name="filter2" options={filter2Options} />
          {/* Submit button */}
          <button type="submit" disabled={isSubmitting}>
            Apply Filter
          </button>
        </form>
      </FormProvider>
    </div>
  );
}

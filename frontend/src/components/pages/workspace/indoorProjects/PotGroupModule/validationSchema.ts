import * as Yup from 'yup';

const validationSchema = Yup.object({
  cameraOrientation: Yup.string()
    .oneOf(['top', 'side'], 'Invalid value')
    .required('Required field'),
  groupBy: Yup.string()
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
});

export default validationSchema;

import * as yup from 'yup';

const schema = yup.object({
  backend: yup
    .string()
    .oneOf(['odm'], 'Backend must be "odm"')
    .required('Backend is required'),
  disclaimer: yup
    .boolean()
    .oneOf([true], 'You must check this box before proceeding')
    .required('Accepting terms is required'),
  orthoResolution: yup
    .number()
    .typeError('Enter a number using only digits (0-9)')
    .min(1.0, 'Ortho resolution must be at least 1.0')
    .max(100.0, 'Ortho resolution must be at most 100.0')
    .required('Ortho resolution is required'),
  pcQuality: yup
    .string()
    .oneOf(
      ['lowest', 'low', 'medium', 'high', 'ultra'],
      'Point cloud quality must be "lowest", "low", "medium", "high", or "ultra"'
    )
    .required('Point cloud quality is required'),
});

export default schema;

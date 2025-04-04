import * as yup from 'yup';

const schema = yup.object({
  alignQuality: yup
    .string()
    .oneOf(
      ['low', 'medium', 'high'],
      'Alignment accuracy must be "low", "medium", or "high"'
    )
    .required('Alignment accuracy is required'),
  backend: yup
    .string()
    .oneOf(['metashape'], 'Backend must be "metashape"')
    .required('Backend is required'),
  buildDepthQuality: yup
    .string()
    .oneOf(
      ['low', 'medium', 'high'],
      'Build depth quality must be "low", "medium", or "high"'
    )
    .required('Build depth quality is required'),
  camera: yup
    .string()
    .oneOf(['single', 'multi'], 'Camera sensors must be single or multi')
    .required('Camera sensors is required'),
  disclaimer: yup
    .boolean()
    .oneOf([true], 'You must check this box before proceeding')
    .required('Accepting terms is required'),
  keyPoint: yup
    .number()
    .typeError('Enter a number using only digits (0-9)')
    .integer('Only whole numbers are allowed')
    .positive('Key point limit must be greater than 0')
    .required('Key point limit is required'),
  tiePoint: yup
    .number()
    .typeError('Enter a number using only digits (0-9)')
    .integer('Only whole numbers are allowed')
    .positive('Tie point limit must be greater than 0')
    .required('Tie point limit is required'),
});

export default schema;

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
  blendingMode: yup
    .string()
    .oneOf(
      ['average', 'disabled', 'min', 'max', 'mosaic'],
      'Blending mode must be "average", "disabled", "min", "max", or "mosaic"'
    )
    .required('Blending mode is required'),
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
  cullFaces: yup.boolean().required('Cull faces is required'),
  disclaimer: yup
    .boolean()
    .oneOf([true], 'You must check this box before proceeding')
    .required('Accepting terms is required'),
  fillHoles: yup.boolean().required('Fill holes is required'),
  ghostingFilter: yup.boolean().required('Ghosting filter is required'),
  keyPoint: yup
    .number()
    .typeError('Enter a number using only digits (0-9)')
    .integer('Only whole numbers are allowed')
    .positive('Key point limit must be greater than 0')
    .required('Key point limit is required'),
  refineSeamlines: yup.boolean().required('Refine seamlines is required'),
  resolution: yup
    .number()
    .typeError('Enter a valid number (decimals allowed)')
    .min(0, 'Resolution must be 0 or greater (0 = auto)')
    .required('Resolution is required'),
  tiePoint: yup
    .number()
    .typeError('Enter a number using only digits (0-9)')
    .integer('Only whole numbers are allowed')
    .positive('Tie point limit must be greater than 0')
    .required('Tie point limit is required'),
});

export default schema;

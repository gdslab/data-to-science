import * as Yup from 'yup';

const scatterValidationSchema = Yup.object({
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
  targetTraitX: Yup.string().required('X trait is required'),
  targetTraitY: Yup.string()
    .required('Y trait is required')
    .test(
      'different-traits',
      'X and Y traits must be different for a scatter plot',
      function (value) {
        return value !== this.parent.targetTraitX;
      }
    ),
});

export default scatterValidationSchema;

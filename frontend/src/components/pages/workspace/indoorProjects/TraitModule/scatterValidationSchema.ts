import * as Yup from 'yup';

const scatterValidationSchema = Yup.object({
  cameraOrientation: Yup.string()
    .oneOf(['top', 'side'], 'Invalid value')
    .required('Required field'),
  plottedBy: Yup.string()
    .oneOf(['groups', 'pots'], 'Invalid value')
    .required('Required field'),
  accordingTo: Yup.string().required('Required field'),
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

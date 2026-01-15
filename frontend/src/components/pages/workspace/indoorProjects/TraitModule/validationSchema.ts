import * as Yup from 'yup';

const validationSchema = Yup.object({
  cameraOrientation: Yup.string()
    .oneOf(['top', 'side'], 'Invalid value')
    .required('Required field'),
  plottedBy: Yup.string()
    .oneOf(['groups', 'pots'], 'Invalid value')
    .required('Required field'),
  accordingTo: Yup.string().required('Required field'),
  targetTrait: Yup.string().required('Required field'),
});

export default validationSchema;

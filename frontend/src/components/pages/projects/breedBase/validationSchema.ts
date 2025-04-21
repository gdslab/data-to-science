import * as yup from 'yup';

const schema = yup.object({
  breedbaseUrl: yup
    .string()
    .url('Invalid URL')
    .required('Required')
    .test('is-https', 'Only HTTPS URLs are allowed', (value) => {
      return value?.startsWith('https://');
    }),
  studyDbIds: yup.string(),
  studyNames: yup.string(),
  trialDbIds: yup.string(),
  trialNames: yup.string(),
});

export default schema;

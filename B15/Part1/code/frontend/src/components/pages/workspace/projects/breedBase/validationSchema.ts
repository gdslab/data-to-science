import * as yup from 'yup';

const schema = yup.object({
  breedbaseUrl: yup
    .string()
    .url('Invalid URL')
    .required('Required')
    .test('is-https', 'Only HTTPS URLs are allowed', (value) => {
      return value?.startsWith('https://');
    }),
  programNames: yup.string(),
  studyDbIds: yup.string(),
  studyNames: yup.string(),
});

export default schema;

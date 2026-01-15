import * as Yup from 'yup';

const step1ValidationSchema = Yup.object({
  newColumns: Yup.array().of(
    Yup.object({
      name: Yup.string()
        .min(1, 'Must have at least 1 character')
        .max(64, 'Cannot exceed 64 characters')
        .required('Required'),
      fill: Yup.string()
        .min(1, 'Must have at least 1 character')
        .max(64, 'Cannot exceed 64 characters')
        .required('Required'),
    })
  ),
});

const step2ValidationSchema = Yup.object({
  treatments: Yup.array()
    .of(
      Yup.object({
        data: Yup.array().of(Yup.object()),
        filenames: Yup.array().of(Yup.string()),
        headers: Yup.array().of(
          Yup.object({ name: Yup.string(), selected: Yup.boolean() })
        ),
        name: Yup.string()
          .min(1, 'Must have at least 1 character')
          .max(64, 'Cannot exceed 64 characters')
          .required('Required'),
      })
    )
    .min(1, 'Must enter at least one treatment')
    .required(),
});

const step3ValidationSchema = Yup.object({
  measurements: Yup.array().of(
    Yup.object({
      name: Yup.string()
        .min(1, 'Must have at least 1 character')
        .max(64, 'Cannot exceed 64 characters')
        .required('Required'),
      units: Yup.string()
        .min(1, 'Must have at least 1 character')
        .max(64, 'Cannot exceed 64 characters'),
      timepoints: Yup.array().of(
        Yup.object({
          numberOfSamples: Yup.number()
            .min(1, 'Must have at least 1 sample')
            .required('Required'),
          sampleNames: Yup.array()
            .of(
              Yup.string()
                .min(1, 'Must have at least 1 character')
                .max(64, 'Cannot exceed 64 characters')
                .required('Required')
            )
            .test('unique', 'Sample names must be unique', (value) =>
              value ? value.length === new Set(value)?.size : true
            )
            .test(
              'matches-num-of-samps',
              'Number of sample names must match "No. of samples" value',
              (value, context) => {
                const { numberOfSamples } = context.parent;
                return (value && value.length === numberOfSamples) || !numberOfSamples;
              }
            ),
          timepointIdentifier: Yup.string()
            .min(1, 'Must have at least 1 character')
            .max(64, 'Cannot exceed 64 characters')
            .required('Required'),
        })
      ),
    })
  ),
});

export { step1ValidationSchema, step2ValidationSchema, step3ValidationSchema };

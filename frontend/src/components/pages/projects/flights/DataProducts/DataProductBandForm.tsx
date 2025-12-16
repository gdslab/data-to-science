import { isAxiosError } from 'axios';
import { useState } from 'react';
import { SubmitHandler, useFieldArray, useForm } from 'react-hook-form';
import { useParams, useRevalidator } from 'react-router';
import * as yup from 'yup';
import { yupResolver } from '@hookform/resolvers/yup';

import HintText from '../../../../HintText';
import { DataProduct, EO } from '../../Project';
import Alert, { Status } from '../../../../Alert';

import api from '../../../../../api';

type DataProductBandFormProps = { dataProduct: DataProduct };

interface DataProductBandForm {
  bands: EO[];
}

const validationSchema = yup.object({
  bands: yup
    .array()
    .of(
      yup.object({
        name: yup.string().required('Band name is required'),
        description: yup.string().required('Band description is required'),
      })
    )
    .required('Bands are required'),
});

export default function DataProductBandForm({
  dataProduct,
}: DataProductBandFormProps) {
  const [status, setStatus] = useState<Status | null>(null);

  const { projectId, flightId } = useParams();
  const revalidator = useRevalidator();

  const { control, formState, handleSubmit, register } =
    useForm<DataProductBandForm>({
      defaultValues: {
        bands: dataProduct.stac_properties.eo,
      },
      resolver: yupResolver(validationSchema),
    });

  const { isSubmitting } = formState;

  const { fields } = useFieldArray({
    control,
    name: 'bands',
  });

  const onSubmit: SubmitHandler<DataProductBandForm> = async (data) => {
    let endpoint = `/projects/${projectId}`;
    endpoint += `/flights/${flightId}/data_products/${dataProduct.id}/bands`;

    try {
      const response = await api.put(endpoint, data);

      if (response.status === 200) {
        setStatus({
          type: 'success',
          msg: 'Band descriptions updated successfully',
        });
        revalidator.revalidate();
        setTimeout(() => setStatus(null), 3000);
      }
    } catch (error) {
      setStatus({ type: 'error', msg: 'Unable to update band descriptions' });
      setTimeout(() => setStatus(null), 3000);
      if (isAxiosError(error)) {
        // Axios-specific error handling
        const status = error.response?.status || 500;
        const message = error.response?.data?.message || error.message;

        throw {
          status,
          message: `Failed to update data product bands: ${message}`,
        };
      } else {
        // Generic error handling
        throw {
          status: 500,
          message: 'An unexpected error occurred.',
        };
      }
    }
  };

  return (
    <form className="flex flex-col gap-2" onSubmit={handleSubmit(onSubmit)}>
      <HintText>Update band descriptions</HintText>
      <div className="grid grid-cols-2 font-semibold text-gray-700">
        <div>Name</div>
        <div>Description</div>
      </div>
      <div className="space-y-4 overflow-y-auto h-40">
        {fields.map((field, index) => (
          <div
            key={field.id}
            className="grid grid-cols-2 gap-4 items-center pr-4"
          >
            <input
              type="text"
              className="text-sm disabled:opacity-50"
              {...register(`bands.${index}.name`)}
              readOnly
              disabled
            />
            <input
              className="text-sm"
              type="text"
              {...register(`bands.${index}.description`)}
            />
          </div>
        ))}
      </div>
      <button
        className="p-4 bg-accent2/90 text-white font-semibold py-1 rounded-sm enabled:hover:bg-accent2 disabled:opacity-75 disabled:cursor-not-allowed"
        type="submit"
        disabled={isSubmitting}
      >
        {isSubmitting ? 'Saving Descriptions...' : 'Save Descriptions'}
      </button>
      {status && <Alert alertType={status.type}>{status.msg}</Alert>}
    </form>
  );
}

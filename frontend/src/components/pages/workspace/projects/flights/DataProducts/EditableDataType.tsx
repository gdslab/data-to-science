import axios, { AxiosResponse, isAxiosError } from 'axios';
import { useState } from 'react';
import { useParams, useRevalidator } from 'react-router-dom';
import Createable from 'react-select/creatable';
import { CheckIcon, PencilIcon, XMarkIcon } from '@heroicons/react/24/outline';

import { DataProduct } from '../../Project';
import { Status } from '../../../../../Alert';

import { useProjectContext } from '../../ProjectContext';

type DataTypeOption = {
  value: string;
  label: string;
};

function getDataTypeOptions(dataProduct: DataProduct): DataTypeOption[] {
  let defaultOptions = [
    { value: 'dsm', label: 'DSM' },
    { value: 'ortho', label: 'Ortho' },
  ];
  // check default options for data product's current data type
  let currentDataType = defaultOptions.findIndex(
    (option) => option.value.toLowerCase() === dataProduct.data_type.toLowerCase()
  );
  // add current data type to options if not already present
  if (currentDataType > -1) {
    return defaultOptions;
  } else {
    defaultOptions.unshift({
      value: dataProduct.data_type.toLowerCase(),
      label: dataProduct.data_type.toUpperCase(),
    });
    return defaultOptions;
  }
}

export default function EditableDataType({
  dataProduct,
  isEditing,
  menuPlacement = 'auto',
  setIsEditing,
  setStatus,
}: {
  dataProduct: DataProduct;
  isEditing: boolean;
  menuPlacement?: 'bottom' | 'auto' | 'top';
  setIsEditing: React.Dispatch<React.SetStateAction<boolean>>;
  setStatus: React.Dispatch<React.SetStateAction<Status | null>>;
}) {
  const [selectedDataType, setSelectedDataType] = useState<string>(
    getDataTypeOptions(dataProduct)[0].value
  );

  const { projectId, flightId } = useParams();
  const revalidator = useRevalidator();

  const { projectRole } = useProjectContext();

  function toggleIsEditing() {
    setIsEditing(!isEditing);
  }

  if (!isEditing) {
    return (
      <div className="flex items-center justify-center gap-2">
        <span>{dataProduct.data_type.split('_').join(' ').toUpperCase()}</span>
        {(projectRole === 'owner' || projectRole === 'manager') &&
          dataProduct.data_type.toLowerCase() !== 'point_cloud' && (
            <button onClick={toggleIsEditing}>
              <PencilIcon className="h-3 w-3" />
            </button>
          )}
      </div>
    );
  }

  async function saveChanges(currentDataType, dataProductId) {
    if (!projectId && !flightId) return;
    if (selectedDataType === currentDataType) return;
    try {
      const response: AxiosResponse<DataProduct> = await axios.put(
        `${
          import.meta.env.VITE_API_V1_STR
        }/projects/${projectId}/flights/${flightId}/data_products/${dataProductId}`,
        { data_type: selectedDataType }
      );
      if (response.status === 200) {
        revalidator.revalidate();
        setIsEditing(false);
      } else {
        setStatus({ type: 'error', msg: 'Unable to change data type name' });
        setIsEditing(false);
      }
    } catch (err) {
      if (isAxiosError(err) && err.response && err.response.data.detail) {
        setStatus({ type: 'error', msg: err.response.data.detail });
      } else {
        setStatus({ type: 'error', msg: 'Unable to change data type name' });
      }
      setIsEditing(false);
    }
  }

  if (isEditing) {
    return (
      <div className="w-full flex justify-between gap-2">
        <div className="w-3/4">
          <Createable
            styles={{
              input: (base) => ({
                ...base,
                'input:focus': {
                  boxShadow: 'none',
                },
              }),
            }}
            theme={(theme) => ({
              ...theme,
              colors: {
                ...theme.colors,
                primary: '#3d5a80',
                primary25: '#e2e8f0',
              },
            })}
            maxMenuHeight={140}
            menuPlacement={menuPlacement}
            isSearchable
            options={getDataTypeOptions(dataProduct)}
            onChange={(newDataType) => {
              if (newDataType && newDataType.value) {
                setSelectedDataType(newDataType.value);
              }
            }}
          />
        </div>
        <div className="w-1/4 flex justify-center gap-4">
          <button
            title="Save changes"
            onClick={() => saveChanges(dataProduct.data_type, dataProduct.id)}
          >
            <CheckIcon className="h-4 w-4" />
          </button>
          <button title="Discard changes" onClick={toggleIsEditing}>
            <XMarkIcon className="h-$ w-4" />
          </button>
        </div>
      </div>
    );
  }
}

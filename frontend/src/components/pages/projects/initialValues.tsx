export interface InitialValues {
  title: string;
  description: string;
  locationId: string;
  plantingDate: string;
  harvestDate: string;
  teamId: string;
}

const initialValues: InitialValues = {
  title: '',
  description: '',
  locationId: '',
  plantingDate: '',
  harvestDate: '',
  teamId: '',
};

export default initialValues;

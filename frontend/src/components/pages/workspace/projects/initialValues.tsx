export interface InitialValues {
  title: string;
  description: string;
  location: object;
  plantingDate: string;
  harvestDate: string;
  teamId: string;
}

const initialValues: InitialValues = {
  title: '',
  description: '',
  location: {},
  plantingDate: '',
  harvestDate: '',
  teamId: '',
};

export default initialValues;

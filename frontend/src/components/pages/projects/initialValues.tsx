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
  location: {
    center_x: 0,
    center_y: 0,
    geom: '',
  },
  plantingDate: '',
  harvestDate: '',
  teamId: '',
};

export default initialValues;

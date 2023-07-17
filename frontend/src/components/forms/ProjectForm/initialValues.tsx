const initialValues = {
  title: "",
  description: "",
  location: {
    type: "Feature",
    geometry: {
      type: "Point",
      coordinates: [125.6, 10.1],
    },
    properties: {
      name: "Dinagat Islands",
    },
  },
  plantingDate: "",
  harvestDate: "",
};

export default initialValues;

import axios from 'axios';
import { Params } from 'react-router-dom';

export async function loader({ params }: { params: Params<string> }) {
  try {
    const rawData = await axios.get(
      `/api/v1/projects/${params.projectId}/flights/${params.flightId}/raw_data`
    );
    if (rawData) {
      return rawData.data;
    } else {
      return [];
    }
  } catch (err) {
    console.error('Unable to retrieve raw data');
    return [];
  }
}

export default function RawData() {
  return <h1>Raw Data</h1>;
}

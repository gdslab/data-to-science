import { useLoaderData, Link } from "react-router-dom";

interface Dataset {
  id: string;
  category: string;
}

export default function DatasetList() {
  const datasets = useLoaderData() as Dataset[];

  return (
    <div>
      {datasets.length > 0 ? (
        <div>
          <h2>Datasets</h2>
          <table>
            <thead>
              <tr>
                <th>Category</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {datasets.map((dataset) => (
                <tr key={dataset.id}>
                  <td>
                    <Link to={`/datasets/${dataset.id}`}>{dataset.category}</Link>
                  </td>
                  <td>X</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <em>No datasets</em>
      )}
    </div>
  );
}

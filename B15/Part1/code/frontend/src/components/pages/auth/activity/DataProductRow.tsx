import { isAxiosError } from 'axios';
import { ReactNode, useState } from 'react';
import { useNavigate } from 'react-router';

import api from '../../../../api';
import { DataProduct, ProjectItem } from '../../workspace/projects/Project';

export default function DataProductRow({
  dataProductId,
  projectName,
  subline,
  projectId,
  rank,
  metric,
}: {
  dataProductId: string;
  projectName: string;
  subline: string;
  projectId: string;
  rank?: number;
  metric: ReactNode;
}) {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);

  // Open the data product in the map workspace, mirroring the "View" action in
  // DataProductCard/DataProductsTable. The map's LayerPane expects the full
  // project and data product objects in navigation state.
  //
  // "Your activity" rows can reference data products in published projects the
  // user is not a member of, so both fetches must work for non-members:
  //  - project: try the member endpoint, then fall back to the public published
  //    endpoint, tagging it is_public (as ProjectLoader does) so the map uses
  //    its public data sources.
  //  - data product: /public/user_access returns the signed data product for
  //    members and public viewers alike.
  async function handleClick() {
    if (isLoading) return;
    setIsLoading(true);
    try {
      let project: ProjectItem;
      try {
        const response = await api.get<ProjectItem>(`/projects/${projectId}`);
        project = response.data;
      } catch {
        const response = await api.get<ProjectItem>(
          `/public/projects/${projectId}`
        );
        project = { ...response.data, is_public: true };
      }
      const dataProductResponse = await api.get<DataProduct>(
        `/public/user_access?file_id=${dataProductId}`
      );
      navigate('/home', {
        state: {
          project,
          dataProduct: dataProductResponse.data,
          navContext: 'dataProductCard',
        },
      });
    } catch (err) {
      if (isAxiosError(err) && err.response) {
        console.error(err.response.data);
      } else {
        console.error(err);
      }
      setIsLoading(false);
    }
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={isLoading}
      className="flex w-full items-center gap-3 rounded-xs p-2 text-left hover:bg-gray-50 disabled:opacity-60"
    >
      {rank !== undefined ? (
        <span className="w-4 shrink-0 text-sm font-semibold text-gray-400">
          {rank}
        </span>
      ) : null}
      <div className="flex min-w-0 flex-1 flex-col">
        <span className="truncate text-sm font-medium text-accent3">
          {projectName}
        </span>
        <span className="truncate text-xs text-gray-500">{subline}</span>
      </div>
      <div className="shrink-0 text-sm">{metric}</div>
    </button>
  );
}

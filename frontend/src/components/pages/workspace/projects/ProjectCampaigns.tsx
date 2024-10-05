import axios, { AxiosResponse } from 'axios';
import { useNavigate, useParams } from 'react-router-dom';

import { Button, LinkButton } from '../../../Buttons';
import { useFieldCampaignContext } from './fieldCampaigns/FieldCampaignContext';
import FieldCampaignTable from './fieldCampaigns/FieldCampaignTable';
import { FieldCampaign } from './Project';
import { useProjectContext } from './ProjectContext';

export default function ProjectCampaigns() {
  const navigate = useNavigate();
  const { projectId } = useParams();

  const { projectRole } = useProjectContext();
  const { fieldCampaign, updateFieldCampaign } = useFieldCampaignContext();

  return (
    <div className="flex flex-col gap-4 pb-4">
      <h2>Field Data</h2>
      {fieldCampaign && fieldCampaign.form_data ? (
        <FieldCampaignTable />
      ) : (
        'No field data has been added.'
      )}
      {fieldCampaign ? (
        <div className="flex justify-center">
          <LinkButton
            size="sm"
            url={`/projects/${projectId}/campaigns/${fieldCampaign.id}`}
          >
            Edit Field Data
          </LinkButton>
        </div>
      ) : null}
      {!fieldCampaign && projectRole !== 'viewer' ? (
        <div className="flex justify-center">
          <Button
            type="button"
            size="sm"
            onClick={async () => {
              try {
                const response: AxiosResponse<FieldCampaign | null> = await axios.post(
                  `${import.meta.env.VITE_API_V1_STR}/projects/${projectId}/campaigns`
                );
                if (response && response.data) {
                  updateFieldCampaign(response.data);
                  navigate(`/projects/${projectId}/campaigns/${response.data.id}`);
                }
              } catch (_err) {
                console.log('unable to retrieve campaign');
              }
            }}
          >
            Add Field Data
          </Button>
        </div>
      ) : null}
    </div>
  );
}

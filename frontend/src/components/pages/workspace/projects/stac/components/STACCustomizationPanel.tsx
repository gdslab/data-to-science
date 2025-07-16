import Alert, { Status } from '../../../../../Alert';
import { Project } from '../../Project';
import ScientificCitationForm from '../ScientificCitationForm';
import STACItemTitlesForm from '../STACItemTitlesForm';
import ActionButtons from '../ActionButtons';
import { STACItem } from '../STACTypes';

interface FormState {
  sciDoi: string;
  sciCitation: string;
  license: string;
  customTitles: Record<string, string>;
}

interface STACCustomizationPanelProps {
  project: Project;
  formState: FormState;
  updateFormField: <K extends keyof FormState>(
    field: K,
    value: FormState[K]
  ) => void;
  stacItems: STACItem[];
  actions: {
    handlePublish: () => void;
    handleUpdate: () => void;
    handleUnpublish: () => void;
  };
  operationStates: {
    isPublishing: boolean;
    isUnpublishing: boolean;
    isUpdating: boolean;
  };
  status: Status | null;
}

export default function STACCustomizationPanel({
  project,
  formState,
  updateFormField,
  stacItems,
  actions,
  operationStates,
  status,
}: STACCustomizationPanelProps) {
  return (
    <div className="lg:col-span-1">
      <h3 className="text-md font-bold mb-4">Customization</h3>

      <ScientificCitationForm
        sciDoi={formState.sciDoi}
        setSciDoi={(value) => updateFormField('sciDoi', value)}
        sciCitation={formState.sciCitation}
        setSciCitation={(value) => updateFormField('sciCitation', value)}
        license={formState.license}
        setLicense={(value) => updateFormField('license', value)}
      />

      <STACItemTitlesForm
        items={stacItems}
        customTitles={formState.customTitles}
        setCustomTitles={(value) => updateFormField('customTitles', value)}
      />

      <ActionButtons
        project={project}
        isPublishing={operationStates.isPublishing}
        isUnpublishing={operationStates.isUnpublishing}
        isUpdating={operationStates.isUpdating}
        onPublish={actions.handlePublish}
        onUpdate={actions.handleUpdate}
        onUnpublish={actions.handleUnpublish}
      />

      {status && (
        <div className="mb-4">
          <Alert alertType={status.type}>{status.msg}</Alert>
        </div>
      )}
    </div>
  );
}

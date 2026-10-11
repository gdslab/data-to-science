import { Button } from '../../Buttons';

import { useAnnotationContext } from '../contexts/AnnotationContext';

const AnnotationInstructions = () => (
  <p className="mt-2 text-sm text-gray-500">
    Use the draw tools on the right side of the map to create an annotation.
  </p>
);

export default function AnnotationsPane() {
  const { active, editingAnnotation, toggle } = useAnnotationContext();

  return (
    <fieldset className="border border-solid border-slate-300 p-2">
      <legend className="block text-sm text-gray-400 font-semibold pt-1 pb-1">
        Annotations
      </legend>
      <Button
        size="sm"
        onClick={toggle}
        icon={editingAnnotation ? undefined : 'plus'}
      >
        {active
          ? editingAnnotation
            ? 'Cancel Redraw'
            : 'Exit Annotation'
          : 'Start Annotation'}
      </Button>
      {active && !editingAnnotation && <AnnotationInstructions />}
      {active && editingAnnotation && (
        <p className="mt-2 text-sm text-amber-600">
          Draw a new shape to replace the geometry for &ldquo;
          {editingAnnotation.description.length > 40
            ? `${editingAnnotation.description.slice(0, 40)}...`
            : editingAnnotation.description}
          &rdquo;.
        </p>
      )}
    </fieldset>
  );
}

import { Popup } from 'react-map-gl/maplibre';

import { PopupInfoProps } from './HomeMap';
import { useMapContext } from './MapContext';

type ProjectPopupProps = {
  popupInfo: PopupInfoProps | { [key: string]: any };
  onClose: () => void;
  showActionButton?: boolean;
};

export default function ProjectPopup({
  popupInfo,
  onClose,
  showActionButton = true,
}: ProjectPopupProps) {
  const { projects, activeProjectDispatch } = useMapContext();

  return (
    <Popup
      anchor="top"
      longitude={popupInfo.longitude}
      latitude={popupInfo.latitude}
      onClose={onClose}
      maxWidth="320px"
    >
      <article className="flex flex-col gap-2 text-wrap w-72">
        <span className="block text-lg text-balance font-bold truncate">
          {popupInfo.feature.properties.title}
        </span>
        <p className="text-pretty">{popupInfo.feature.properties.title}</p>
        {showActionButton && (
          <button
            className="px-4 py-2 bg-blue-500 text-white rounded-sm hover:bg-blue-600 focus:outline-hidden focus:ring-2 focus:ring-blue-300"
            onClick={() => {
              const thisProject = projects?.filter(
                ({ id }) => id === popupInfo.feature.properties.id
              );
              if (thisProject && thisProject.length === 1) {
                activeProjectDispatch({ type: 'set', payload: thisProject[0] });
                onClose();
              }
            }}
          >
            Open
          </button>
        )}
      </article>
    </Popup>
  );
}

import { useState, useEffect } from 'react';
import { useParams } from 'react-router';

import { AlertBar } from '../../Alert';
import MapLayerUpload from './mapLayers/MapLayerUpload';
import MapLayersTable from './mapLayers/MapLayersTable';
import { getMapLayers, useProjectContext } from './ProjectContext';

import { useInterval } from '../../hooks';

export default function ProjectVectorData() {
  const { mapLayers, mapLayersDispatch, projectRole } = useProjectContext();
  const { projectId } = useParams();

  const [pendingUpload, setPendingUpload] = useState(false);
  const [layerCount, setLayerCount] = useState(0);

  // Conditional polling: 5s when upload pending, 30s otherwise
  useInterval(
    () => {
      if (projectId) {
        getMapLayers(projectId, mapLayersDispatch);
      }
    },
    pendingUpload ? 5000 : 30000
  );

  // Detect when new layer appears and clear pending flag
  useEffect(() => {
    if (mapLayers.length > layerCount && pendingUpload) {
      // New layer appeared, clear pending flag
      setPendingUpload(false);
    }
    setLayerCount(mapLayers.length);
  }, [mapLayers.length, layerCount, pendingUpload]);

  // Timeout to clear pending flag after 2 minutes
  useEffect(() => {
    if (pendingUpload) {
      const timer = setTimeout(() => {
        setPendingUpload(false);
      }, 120000); // 2 minutes
      return () => clearTimeout(timer);
    }
  }, [pendingUpload]);

  return (
    <div className="mb-4">
      <h2>Map Layers</h2>
      {pendingUpload && (
        <AlertBar alertType="info">
          Map layer upload is being processed - checking for updates...
        </AlertBar>
      )}
      <div className="flex flex-col gap-4">
        {mapLayers.length > 0 && <MapLayersTable />}
        {mapLayers.length === 0 &&
          (projectRole !== 'viewer' ? (
            <span>Use the below button to add your first map layer.</span>
          ) : (
            <span>No map layers have been added.</span>
          ))}
        {projectRole !== 'viewer' ? (
          <MapLayerUpload onUploadSuccess={() => setPendingUpload(true)} />
        ) : null}
      </div>
    </div>
  );
}

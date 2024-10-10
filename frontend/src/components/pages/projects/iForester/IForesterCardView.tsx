import { useEffect, useState } from 'react';

import { useIForesterControlContext } from './IForesterContext';
import { getUniqueValues } from './IForesterMap';
import { IForester } from '../Project';
import { useProjectContext } from '../ProjectContext';
import IForesterCard from './IForesterCard';

export default function IForesterCardView() {
  const [filteredLocations, setFilteredLocations] = useState<IForester[]>([]);
  const { state, dispatch } = useIForesterControlContext();
  const { dbhMin, dbhMax, speciesSelection, visibleMarkers } = state;
  const { iforester } = useProjectContext();

  // set initial selected species
  useEffect(() => {
    if (iforester && iforester.length > 0 && speciesSelection.length === 0) {
      dispatch({
        type: 'SET_SPECIES_SELECTION',
        payload: getUniqueValues(
          iforester.map(({ species }) => species.toLowerCase())
        ) as string[],
      });
    }
  }, [iforester]);

  // set initial DBH min and DBH max
  useEffect(() => {
    if (iforester && iforester.length > 0) {
      if (dbhMin === -1) {
        dispatch({
          type: 'SET_DBH_MIN',
          payload: Math.min.apply(
            Math,
            iforester.map(({ dbh }) => dbh)
          ),
        });
      }
      if (dbhMax === -1) {
        dispatch({
          type: 'SET_DBH_MAX',
          payload: Math.max.apply(
            Math,
            iforester.map(({ dbh }) => dbh)
          ),
        });
      }
    }
  });

  useEffect(() => {
    if (iforester && iforester.length > 0) {
      setFilteredLocations(
        iforester.filter(
          ({ id, dbh, species }) =>
            dbh >= dbhMin &&
            dbh <= dbhMax &&
            speciesSelection.includes(species.toLowerCase()) &&
            visibleMarkers.includes(id)
        )
      );
    }
  }, [dbhMin, dbhMax, iforester, speciesSelection, visibleMarkers]);

  if (iforester && iforester.length === 0) {
    return <div className="mx-4 my-2">No data added yet</div>;
  }

  return (
    <div className="flex justify-center">
      {filteredLocations.length > 0 ? (
        <div className="w-full pb-2 pr-2.5 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-2.5 max-h-[calc(100vh_-_64px_-_52px_-_52px)] overflow-y-auto">
          {filteredLocations.map((location) => (
            <IForesterCard key={location.id} submission={location} />
          ))}
        </div>
      ) : (
        <span>No cards to display. Check Filter Options on map.</span>
      )}
    </div>
  );
}

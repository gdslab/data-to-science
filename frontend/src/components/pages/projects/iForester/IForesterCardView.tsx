import { useEffect, useMemo, useState } from 'react';

import { IForester } from '../Project';
import { useIForesterControlContext } from './IForesterContext';
import { getUniqueValues } from './IForesterMap';
import { useProjectContext } from '../ProjectContext';
import IForesterCard from './IForesterCard';
import PaginationList from '../../../PaginationList';

export default function IForesterCardView() {
  const [pageData, setPageData] = useState<IForester[]>([]);
  const { state, dispatch } = useIForesterControlContext();
  const { dbhMin, dbhMax, speciesSelection, visibleMarkers } = state;
  const { iforester } = useProjectContext();

  // Set initial selected species
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

  // Set initial DBH min and DBH max
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

  if (iforester && iforester.length === 0) {
    return <div className="mx-4 my-2">No data added yet</div>;
  }

  // Filter and sort IForester data based on DBH and species selection
  const sortedFilteredLocations = useMemo(() => {
    if (!iforester || iforester.length === 0) return [];

    return iforester
      .filter(
        ({ id, dbh, species }) =>
          dbh >= dbhMin &&
          dbh <= dbhMax &&
          speciesSelection.includes(species.toLowerCase()) &&
          visibleMarkers.includes(id)
      )
      .sort((a, b) => {
        const dateA = new Date(a.timeStamp.split('.')[0]);
        const dateB = new Date(b.timeStamp.split('.')[0]);

        if (dateA < dateB) return 1;
        if (dateA > dateB) return -1;

        return a.dbh - b.dbh;
      });
  }, [dbhMin, dbhMax, iforester, speciesSelection, visibleMarkers]);

  const updatePageData = (pageData: IForester[]) => {
    setPageData(pageData);
  };

  return (
    <div className="h-full flex justify-center">
      {sortedFilteredLocations.length > 0 ? (
        <PaginationList
          dataList={sortedFilteredLocations}
          updatePageData={updatePageData}
        >
          <div className="w-full pb-2 pr-2.5 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-2.5 max-h-[calc(100vh_-_64px_-_52px_-_52px)]">
            {pageData.map((location) => (
              <IForesterCard key={location.id} submission={location} />
            ))}
          </div>
        </PaginationList>
      ) : (
        <span>No cards to display. Check Filter Options on map.</span>
      )}
    </div>
  );
}

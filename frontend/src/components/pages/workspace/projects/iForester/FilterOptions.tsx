import { useCallback, useEffect, useState } from 'react';
import Select from 'react-select';
import {
  ArrowPathIcon,
  ChevronUpIcon,
  ChevronDownIcon,
} from '@heroicons/react/24/outline';

import { useIForesterControlContext } from './IForesterContext';
import { getUniqueValues } from './IForesterMap';
import FilterSlider from './FilterSlider';
import { useProjectContext } from '../ProjectContext';

type HideShowButton = {
  label: string;
  visible: boolean;
  toggleVisibility: () => void;
};

function HideShowButton({ label, visible, toggleVisibility }: HideShowButton) {
  return (
    <button
      type="button"
      aria-label={visible ? `Hide ${label}` : `Show ${label}`}
      onClick={toggleVisibility}
    >
      {visible ? (
        <ChevronUpIcon className="h-4 w-4" />
      ) : (
        <ChevronDownIcon className="h-4 w-4" />
      )}
    </button>
  );
}

export default function FilterOptions() {
  const { state, dispatch } = useIForesterControlContext();
  const {
    dbhMin,
    dbhMax,
    dbhVisibility,
    // heightMin,
    // heightMax,
    heightVisibility,
    speciesSelection,
    speciesVisibility,
  } = state;

  const [speciesOptions, setSpeciesOptions] = useState<
    { label: string; value: string }[]
  >([]);

  const { iforester } = useProjectContext();

  const updateDBHMin = useCallback(
    (newDBHMin: number) => {
      dispatch({ type: 'SET_DBH_MIN', payload: newDBHMin });
    },
    [dispatch]
  );

  const updateDBHMax = useCallback(
    (newDBHMax: number) => {
      dispatch({ type: 'SET_DBH_MAX', payload: newDBHMax });
    },
    [dispatch]
  );

  const toggleDBHVisibility = useCallback(() => {
    if (heightVisibility) {
      dispatch({ type: 'SET_HEIGHT_VISIBILITY', payload: !heightVisibility });
    }
    if (speciesVisibility) {
      dispatch({ type: 'SET_SPECIES_VISIBILITY', payload: !speciesVisibility });
    }
    dispatch({ type: 'SET_DBH_VISIBILITY', payload: !dbhVisibility });
  }, [dbhVisibility, dispatch, heightVisibility, speciesVisibility]);

  // const updateHeightMin = (newHeightMin) => {
  //   dispatch({ type: 'SET_HEIGHT_MIN', payload: newHeightMin });
  // };

  // const updateHeightMax = (newHeightMax) => {
  //   dispatch({ type: 'SET_HEIGHT_MAX', payload: newHeightMax });
  // };

  // const toggleHeightVisibility = () => {
  //   if (dbhVisibility) {
  //     dispatch({ type: 'SET_DBH_VISIBILITY', payload: !dbhVisibility });
  //   }

  //   if (speciesVisibility) {
  //     dispatch({ type: 'SET_SPECIES_VISIBILITY', payload: !speciesVisibility });
  //   }
  //   dispatch({ type: 'SET_HEIGHT_VISIBILITY', payload: !heightVisibility });
  // };

  const updateSpecies = useCallback(
    (newSpecies: string[]) => {
      dispatch({ type: 'SET_SPECIES_SELECTION', payload: newSpecies });
    },
    [dispatch]
  );

  const toggleSpeciesVisibility = useCallback(() => {
    if (dbhVisibility) {
      dispatch({ type: 'SET_DBH_VISIBILITY', payload: !dbhVisibility });
    }
    if (heightVisibility) {
      dispatch({ type: 'SET_HEIGHT_VISIBILITY', payload: !heightVisibility });
    }
    dispatch({ type: 'SET_SPECIES_VISIBILITY', payload: !speciesVisibility });
  }, [dbhVisibility, dispatch, heightVisibility, speciesVisibility]);

  const getUniqueSpecies = useCallback((): string[] => {
    if (iforester && iforester.length > 0) {
      const uniqueSpecies = getUniqueValues(
        iforester.map(({ species }) => species.toLowerCase())
      ) as string[];
      return uniqueSpecies;
    } else {
      return [''];
    }
  }, [iforester]);

  const updateSpeciesOptions = useCallback(
    () =>
      setSpeciesOptions(
        getUniqueSpecies().map((v) => ({
          label: v as string,
          value: (v as string).toLowerCase(),
        }))
      ),
    [getUniqueSpecies]
  );

  const handleReset = useCallback(() => {
    dispatch({ type: 'SET_DBH_MIN', payload: -1 });
    dispatch({ type: 'SET_DBH_MAX', payload: -1 });
    dispatch({ type: 'SET_HEIGHT_MIN', payload: -1 });
    dispatch({ type: 'SET_HEIGHT_MAX', payload: -1 });
    dispatch({
      type: 'SET_SPECIES_SELECTION',
      payload: getUniqueSpecies(),
    });
    updateSpeciesOptions();
  }, [dispatch, getUniqueSpecies, updateSpeciesOptions]);

  useEffect(() => {
    if (iforester && iforester.length > 0) {
      updateSpeciesOptions();
    }
  }, [iforester, updateSpeciesOptions]);

  return (
    <div className="px-2 p-2 w-44">
      <div className="h-full flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <span className="text-lg font-bold">Filters</span>
          <button
            type="button"
            className="text-slate-500 hover:text-slate-800"
            aria-label="Restore defaults"
            onClick={handleReset}
          >
            <ArrowPathIcon className="h-4 w-4" />
          </button>
        </div>
        {!iforester && <span>Loading...</span>}
        {iforester && iforester.length === 0 && <span>No data added yet</span>}
        {iforester && iforester.length > 0 && (
          <>
            <div className="relative">
              <div className="flex items-center justify-between">
                <span className="text-md font-bold">DBH (m)</span>
                <HideShowButton
                  label="DBH"
                  visible={dbhVisibility}
                  toggleVisibility={toggleDBHVisibility}
                />
              </div>
              {dbhVisibility && (
                <FilterSlider
                  key={iforester.length.toString()}
                  name="dbh"
                  label="DBH"
                  minThumb={dbhMin}
                  maxThumb={dbhMax}
                  unit="m"
                  updateMinThumb={updateDBHMin}
                  updateMaxThumb={updateDBHMax}
                  values={iforester.map(({ dbh }) => dbh)}
                />
              )}
            </div>
            {/* <div className="-mx-2 border-t border-gray-300"></div>
            <div className="relative">
              <div className="flex items-center justify-between">
                <span className="text-md font-bold">Height (ft)</span>
                <HideShowButton
                  label="Height"
                  visible={heightVisibility}
                  toggleVisibility={toggleHeightVisibility}
                />
              </div>
              {heightVisibility && (
                <FilterSlider
                  name="height"
                  label="Height"
                  minThumb={dbhMin}
                  maxThumb={dbhMax}
                  unit="ft"
                  updateMinThumb={updateHeightMin}
                  updateMaxThumb={updateHeightMax}
                  values={iforester.map(({ dbh }) => dbh)}
                />
              )}
            </div> */}
            <div className="-mx-2 border-t border-gray-300"></div>
            <div className="relative">
              <div className="flex items-center justify-between pb-2">
                <span className="text-md font-bold">Species</span>
                <HideShowButton
                  label="Species"
                  visible={speciesVisibility}
                  toggleVisibility={toggleSpeciesVisibility}
                />
              </div>
              {speciesVisibility && (
                <Select
                  id="species"
                  name="species"
                  className="basic-multi-select"
                  classNamePrefix="select"
                  styles={{
                    input: (base) => ({
                      ...base,
                      'input:focus': {
                        boxShadow: 'none',
                      },
                    }),
                    menuPortal: (base) => ({
                      ...base,
                      zIndex: 9999,
                      fontFamily:
                        '"Helvetica Neue", Arial, Helvetica, sans-serif',
                      fontSize: '0.75rem',
                      lineHeight: 1.5,
                    }),
                  }}
                  theme={(theme) => ({
                    ...theme,
                    colors: {
                      ...theme.colors,
                      primary: '#3d5a80',
                      primary25: '#e2e8f0',
                    },
                  })}
                  menuPortalTarget={document.body}
                  isMulti={true}
                  defaultValue={speciesSelection.map((v) => ({
                    label: v as string,
                    value: (v as string).toLowerCase(),
                  }))}
                  options={speciesOptions}
                  onChange={(newSpecies) => {
                    updateSpecies(newSpecies.map(({ value }) => value));
                  }}
                />
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

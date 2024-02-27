import { Flight } from '../Project';

import { FlightAction } from './actions';

export function flightReducer(state: Flight | null, action: FlightAction) {
  switch (action.type) {
    case 'set': {
      return action.payload;
    }
    case 'clear': {
      return null;
    }
    default: {
      return state;
    }
  }
}

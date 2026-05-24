import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useReducer,
  useRef,
  useState,
} from 'react';
import { isAxiosError } from 'axios';
import { Feature } from 'geojson';

import api from '../../../api';
import { useMapContext } from '../MapContext';
import { isPublicOnly } from '../utils';

export interface AnnotationTag {
  tag: { name: string } | null;
}

export interface AnnotationAttachment {
  id: string;
  original_filename: string;
  filepath: string;
  content_type: string;
  size_bytes: number;
  width_px: number | null;
  height_px: number | null;
  duration_seconds: number | null;
  annotation_id: string;
  created_at: string;
  updated_at: string;
}

export type Visibility = 'OWNER' | 'PROJECT';

export interface Annotation {
  id: string;
  description: string;
  geom: Feature;
  visibility: Visibility;
  style: AnnotationStyle | null;
  created_at: string;
  updated_at: string;
  created_by: { id: string } | null;
  tag_rows: AnnotationTag[];
  attachments: AnnotationAttachment[];
}

export interface AnnotationStyle {
  color: string;
  fill: string;
  opacity: number;
}

const DEFAULT_COLOR = '#f97316'; // orange-500
const DEFAULT_FILL = '#fdba74'; // orange-300

export const defaultAnnotationStyle: AnnotationStyle = {
  color: DEFAULT_COLOR,
  fill: DEFAULT_FILL,
  opacity: 100,
};

type State = {
  active: boolean;
  annotations: Annotation[];
  checkedIds: Set<string>;
  styles: Record<string, AnnotationStyle>;
  loading: boolean;
  error: string | null;
};

type Action =
  | { type: 'ACTIVATE' }
  | { type: 'DEACTIVATE' }
  | { type: 'TOGGLE' }
  | { type: 'SET_ANNOTATIONS'; payload: Annotation[] }
  | { type: 'TOGGLE_CHECKED'; payload: string }
  | {
      type: 'UPDATE_STYLE';
      payload: { id: string; property: keyof AnnotationStyle; value: string | number };
    }
  | { type: 'FETCH_START' }
  | { type: 'FETCH_ERROR'; payload: string }
  | { type: 'CLEAR' };

const initialState: State = {
  active: false,
  annotations: [],
  checkedIds: new Set(),
  styles: {},
  loading: false,
  error: null,
};

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'ACTIVATE':
      return { ...state, active: true };
    case 'DEACTIVATE':
      return { ...state, active: false };
    case 'TOGGLE':
      return { ...state, active: !state.active };
    case 'FETCH_START':
      return { ...state, loading: true, error: null };
    case 'SET_ANNOTATIONS': {
      const styles: Record<string, AnnotationStyle> = {};
      for (const a of action.payload) {
        styles[a.id] = state.styles[a.id] || a.style || { ...defaultAnnotationStyle };
      }
      return {
        ...state,
        annotations: action.payload,
        checkedIds: new Set(action.payload.map((a) => a.id)),
        styles,
        loading: false,
        error: null,
      };
    }
    case 'FETCH_ERROR':
      return { ...state, loading: false, error: action.payload };
    case 'TOGGLE_CHECKED': {
      const next = new Set(state.checkedIds);
      if (next.has(action.payload)) {
        next.delete(action.payload);
      } else {
        next.add(action.payload);
      }
      return { ...state, checkedIds: next };
    }
    case 'UPDATE_STYLE': {
      const { id, property, value } = action.payload;
      const current = state.styles[id] || { ...defaultAnnotationStyle };
      return {
        ...state,
        styles: {
          ...state.styles,
          [id]: { ...current, [property]: value },
        },
      };
    }
    case 'CLEAR':
      return {
        ...state,
        annotations: [],
        checkedIds: new Set(),
        styles: {},
        loading: false,
        error: null,
      };
    default:
      return state;
  }
}

type Ctx = {
  active: boolean;
  activate: () => void;
  deactivate: () => void;
  toggle: () => void;
  annotations: Annotation[];
  checkedIds: Set<string>;
  styles: Record<string, AnnotationStyle>;
  loading: boolean;
  error: string | null;
  toggleChecked: (id: string) => void;
  updateStyle: (
    id: string,
    property: keyof AnnotationStyle,
    value: string | number
  ) => void;
  editingAnnotation: Annotation | null;
  setEditingAnnotation: (annotation: Annotation | null) => void;
  hoveredAnnotationId: string | null;
  setHoveredAnnotationId: (id: string | null) => void;
  selectedAnnotationId: string | null;
  setSelectedAnnotationId: (id: string | null) => void;
  visible: boolean;
  setVisible: (visible: boolean) => void;
  refetch: () => void;
};

const AnnotationContext = createContext<Ctx | null>(null);

export function AnnotationProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [state, dispatch] = useReducer(reducer, initialState);
  const [editingAnnotation, setEditingAnnotation] = useState<Annotation | null>(null);
  const [hoveredAnnotationId, setHoveredAnnotationId] = useState<string | null>(null);
  const [selectedAnnotationId, setSelectedAnnotationId] = useState<string | null>(null);
  const [visible, setVisible] = useState(false);
  const { activeDataProduct, activeProject } = useMapContext();

  const deactivate = useCallback(() => {
    dispatch({ type: 'DEACTIVATE' });
    setEditingAnnotation(null);
  }, []);

  const fetchAnnotations = useCallback(
    async (signal?: AbortSignal) => {
      if (!activeProject || !activeDataProduct || isPublicOnly(activeProject)) {
        dispatch({ type: 'CLEAR' });
        return;
      }
      dispatch({ type: 'FETCH_START' });
      try {
        const { data } = await api.get<Annotation[]>(
          `/projects/${activeProject.id}/flights/${activeDataProduct.flight_id}/data_products/${activeDataProduct.id}/annotations`,
          { signal }
        );
        dispatch({ type: 'SET_ANNOTATIONS', payload: data });
      } catch (err) {
        if (signal?.aborted) return;
        if (isAxiosError(err)) {
          dispatch({
            type: 'FETCH_ERROR',
            payload:
              err.response?.data.detail || 'Unable to fetch annotations',
          });
        } else {
          dispatch({
            type: 'FETCH_ERROR',
            payload: 'Unable to fetch annotations',
          });
        }
      }
    },
    [activeProject, activeDataProduct]
  );

  useEffect(() => {
    const controller = new AbortController();
    fetchAnnotations(controller.signal);
    return () => controller.abort();
  }, [fetchAnnotations]);

  // Reset visibility when the active data product changes
  useEffect(() => {
    setVisible(false);
  }, [activeDataProduct]);

  // Debounced style persistence — saves to API 500ms after last change
  const saveTimersRef = useRef<Record<string, ReturnType<typeof setTimeout>>>({});
  const stylesRef = useRef(state.styles);
  stylesRef.current = state.styles;

  const debouncedSaveStyle = useCallback(
    (annotationId: string) => {
      if (!activeProject || !activeDataProduct || isPublicOnly(activeProject)) return;
      clearTimeout(saveTimersRef.current[annotationId]);
      saveTimersRef.current[annotationId] = setTimeout(() => {
        const style = stylesRef.current[annotationId];
        if (!style) return;
        api
          .put(
            `/projects/${activeProject.id}/flights/${activeDataProduct.flight_id}/data_products/${activeDataProduct.id}/annotations/${annotationId}`,
            { style }
          )
          .catch((err) => console.error('Failed to save annotation style', err));
      }, 500);
    },
    [activeProject, activeDataProduct]
  );

  // Clean up pending timers on unmount
  useEffect(() => {
    const timers = saveTimersRef.current;
    return () => {
      Object.values(timers).forEach(clearTimeout);
    };
  }, []);

  const value = useMemo<Ctx>(
    () => ({
      active: state.active,
      activate: () => dispatch({ type: 'ACTIVATE' }),
      deactivate,
      toggle: () => {
        if (state.active) {
          deactivate();
        } else {
          dispatch({ type: 'ACTIVATE' });
        }
      },
      annotations: state.annotations,
      checkedIds: state.checkedIds,
      styles: state.styles,
      loading: state.loading,
      error: state.error,
      toggleChecked: (id: string) =>
        dispatch({ type: 'TOGGLE_CHECKED', payload: id }),
      updateStyle: (
        id: string,
        property: keyof AnnotationStyle,
        value: string | number
      ) => {
        dispatch({ type: 'UPDATE_STYLE', payload: { id, property, value } });
        debouncedSaveStyle(id);
      },
      editingAnnotation,
      setEditingAnnotation,
      hoveredAnnotationId,
      setHoveredAnnotationId,
      selectedAnnotationId,
      setSelectedAnnotationId,
      visible,
      setVisible,
      refetch: () => fetchAnnotations(),
    }),
    [state, editingAnnotation, hoveredAnnotationId, selectedAnnotationId, deactivate, debouncedSaveStyle, visible, fetchAnnotations]
  );

  return (
    <AnnotationContext.Provider value={value}>
      {children}
    </AnnotationContext.Provider>
  );
}

export function useAnnotationContext() {
  const ctx = useContext(AnnotationContext);
  if (!ctx)
    throw new Error(
      'useAnnotationContext must be used within AnnotationProvider'
    );
  return ctx;
}

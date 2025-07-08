import { createContext, useContext, useState, ReactNode } from 'react';

export type Shape = 'circle' | 'rounded-square' | 'hexagon' | 'diamond';

interface ShapeContextType {
  shapes: Record<string, Shape>;
  setShape: (treatment: string, shape: Shape) => void;
}

const ShapeContext = createContext<ShapeContextType | undefined>(undefined);

export function ShapeProvider({
  children,
  treatments,
}: {
  children: ReactNode;
  treatments: string[];
}) {
  // Initialize shapes for each treatment
  const initialShapes = treatments.reduce(
    (acc, treatment) => ({
      ...acc,
      [treatment]: 'circle',
    }),
    {}
  );

  const [shapes, setShapes] = useState<Record<string, Shape>>(initialShapes);

  const setShape = (treatment: string, shape: Shape) => {
    setShapes((prev) => ({
      ...prev,
      [treatment]: shape,
    }));
  };

  return (
    <ShapeContext.Provider value={{ shapes, setShape }}>
      {children}
    </ShapeContext.Provider>
  );
}

export function useShapeContext() {
  const context = useContext(ShapeContext);
  if (context === undefined) {
    throw new Error('useShapeContext must be used within a ShapeProvider');
  }
  return context;
}

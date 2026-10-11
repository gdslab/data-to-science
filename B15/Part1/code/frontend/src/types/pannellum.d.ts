declare global {
  interface Window {
    pannellum: {
      viewer: (
        container: HTMLElement | null,
        config: {
          type: string;
          panorama: string;
          autoLoad: boolean;
        }
      ) => void;
    };
  }
}

export {};

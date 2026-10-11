export default function PlayCanvasglTFViewer({ src }: { src: string }) {
  const url = `/pc-gltf-viewer/?load=${encodeURIComponent(src)}`;
  return <iframe src={url} width="100%" height="100%" />;
}

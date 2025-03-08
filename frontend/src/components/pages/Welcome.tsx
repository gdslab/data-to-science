import brandLogo from '../../assets/d2s-logo-blue.svg';

export default function Welcome({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-2 items-center jusitfy-center m-4">
      <div className="flex items-center justify-center">
        <img
          className="max-h-12 max-w-full h-auto object-contain"
          src={brandLogo}
          alt="Brand Logo"
        />
      </div>
      <div className="text-center">
        <h1 className="text-black mb-0">Welcome!</h1>
        <span className="text-sm text-black">{children}</span>
      </div>
    </div>
  );
}

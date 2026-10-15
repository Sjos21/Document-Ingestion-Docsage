type NavbarProps = {
  onLogout: () => void;
};

export function Navbar({ onLogout }: NavbarProps) {
  return (
    <header className="h-14 border-b border-border flex items-center px-4 justify-between shrink-0">
      <span className="font-medium text-sm">DocSage</span>

      <div className="flex items-center gap-4">
        <span className="text-xs text-muted font-mono">Healthy</span>

        <button
          type="button"
          onClick={onLogout}
          className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-black hover:bg-gray-100 transition-colors"
        >
          Log out
        </button>
      </div>
    </header>
  );
}

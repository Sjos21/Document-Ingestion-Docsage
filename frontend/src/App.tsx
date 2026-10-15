import { useEffect, useState } from "react";
import { AuthPage } from "./components/AuthPage";
import { Navbar } from "./components/Navbar";
import { Sidebar } from "./components/Sidebar";
import { ChatArea } from "./components/ChatArea";
import {
  clearAuthTokens,
  getAccessToken,
  isAuthenticated,
  logout,
} from "./lib/api";

export default function App() {
  const [authenticated, setAuthenticated] = useState(isAuthenticated());

  useEffect(() => {
    const handleUnauthorized = () => {
      clearAuthTokens();
      setAuthenticated(false);
    };

    window.addEventListener("docsage:unauthorized", handleUnauthorized);

    return () => {
      window.removeEventListener("docsage:unauthorized", handleUnauthorized);
    };
  }, []);

  async function handleLogout() {
    await logout();
    setAuthenticated(false);
  }

  if (!authenticated || !getAccessToken()) {
    return (
      <AuthPage onAuthenticated={() => setAuthenticated(true)} />
    );
  }

  return (
    <div className="h-screen flex flex-col">
      <Navbar onLogout={handleLogout}/>
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <ChatArea />
      </div>
    </div>
  );
}

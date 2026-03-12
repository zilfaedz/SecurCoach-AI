import { useState } from "react";
import LoginLayout from "./layout/LoginLayout";
import SignupLayout from "./layout/SignupLayout";

function App() {
  const [authMode, setAuthMode] = useState("login");

  if (authMode === "signup") {
    return <SignupLayout onSwitchToLogin={() => setAuthMode("login")} />;
  }

  return <LoginLayout onSwitchToSignup={() => setAuthMode("signup")} />;
}

export default App;

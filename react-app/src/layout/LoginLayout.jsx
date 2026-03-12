import { useState } from "react";
import "./AuthLayout.css";
import "./LoginLayout.css";
import { signInUser } from "./supabase";

const STREAMLIT_URL = process.env.REACT_APP_STREAMLIT_URL || "http://localhost:8501";

function BrandIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <path d="M12 2L3 7v5c0 5.25 3.75 10.15 9 11.35C17.25 22.15 21 17.25 21 12V7L12 2z" fill="#222831" />
      <path d="M9 12l2 2 4-4" stroke="#948979" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function EmailIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
    </svg>
  );
}

function LockIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
    </svg>
  );
}

function EyeOpenIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
    </svg>
  );
}

function EyeClosedIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
    </svg>
  );
}

function LoginLayout({ onSwitchToSignup }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (!email.trim() || !password) {
      setError("Enter your email and password.");
      return;
    }

    setLoading(true);

    try {
      await signInUser({ email, password });
      setSuccess("Signed in successfully. Redirecting to Streamlit...");
      const target = `${STREAMLIT_URL.replace(/\/+$/, "")}/?auth_email=${encodeURIComponent(
        email.trim().toLowerCase()
      )}`;
      window.location.assign(target);
    } catch (signInError) {
      setError(signInError.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="auth-page login-page">
      <div className="auth-bg-layer" />
      <div className="auth-grain" />
      <div className="auth-deco-line h l" />
      <div className="auth-deco-line h r" />

      <section className="auth-card-wrap">
        <aside className="auth-panel-left">
          <div className="auth-brand-badge">
            <div className="auth-brand-icon">
              <BrandIcon />
            </div>
            <span className="auth-brand-label">SecurCoach AI</span>
          </div>

          <div className="auth-left-headline">
            <h1 className="auth-app-name">
              Train Smarter.
              <br />
              <span>Perform</span>
              <br />
              Better.
            </h1>
            <p className="auth-app-tagline">
              Your AI-powered coaching companion - built for athletes who take
              performance seriously.
            </p>
          </div>

          <p className="auth-left-footer">(C) 2025 SecurCoach AI - All rights reserved</p>
        </aside>

        <section className="auth-panel-right">
          <div className="auth-form-header">
            <h2 className="auth-form-title">Login</h2>
            <p className="auth-form-subtitle">
              Welcome back. Enter your credentials
              <br />
              to access your dashboard.
            </p>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="auth-field">
              <label htmlFor="email">Email</label>
              <div className="auth-input-wrap">
                <input
                  className="auth-input"
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  autoComplete="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                />
                <EmailIcon />
              </div>
            </div>

            <div className="auth-field">
              <label htmlFor="password">Password</label>
              <div className="auth-input-wrap">
                <input
                  id="password"
                  className="auth-input auth-password-input"
                  type={showPassword ? "text" : "password"}
                  placeholder="********"
                  autoComplete="current-password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                />
                <LockIcon />
                <button
                  type="button"
                  className="auth-eye-btn"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  onClick={() => setShowPassword((current) => !current)}
                >
                  {showPassword ? <EyeClosedIcon /> : <EyeOpenIcon />}
                </button>
              </div>
            </div>

            <div className="auth-row-opts">
              <label className="auth-checkbox" htmlFor="remember-me">
                <input
                  id="remember-me"
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(event) => setRememberMe(event.target.checked)}
                />
                <span>Remember me</span>
              </label>
              <a href="/" className="auth-link" onClick={(event) => event.preventDefault()}>
                Forgot password?
              </a>
            </div>

            {error ? <div className="auth-message error">{error}</div> : null}
            {success ? <div className="auth-message success">{success}</div> : null}

            <button type="submit" className="auth-button" disabled={loading}>
              {loading ? "Signing in..." : "Login"}
            </button>

            <div className="auth-divider">
              <span />
              <p>or continue with</p>
              <span />
            </div>

            <p className="auth-inline-note">
              Don&apos;t have an account?{" "}
              <button type="button" className="login-switch-link" onClick={onSwitchToSignup}>
                Sign up
              </button>
            </p>
          </form>
        </section>
      </section>
    </main>
  );
}

export default LoginLayout;

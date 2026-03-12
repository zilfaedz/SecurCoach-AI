import { useState } from "react";
import "./AuthLayout.css";
import "./SignupLayout.css";
import { signUpUser } from "./supabase";

function BrandIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <path d="M12 2L3 7v5c0 5.25 3.75 10.15 9 11.35C17.25 22.15 21 17.25 21 12V7L12 2z" fill="#222831" />
      <path d="M9 12l2 2 4-4" stroke="#948979" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function UserIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6.75a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.5 20.118a7.5 7.5 0 0115 0A17.933 17.933 0 0112 21.75a17.933 17.933 0 01-7.5-1.632z" />
    </svg>
  );
}

function AtIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 9.348V9.75a4.5 4.5 0 11-2.34-3.94m2.34 3.538V9.75a4.5 4.5 0 102.25 3.897V13.5A2.25 2.25 0 0116.5 15.75h-.75" />
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

function SignupLayout({ onSwitchToLogin }) {
  const [form, setForm] = useState({
    name: "",
    username: "",
    email: "",
    password: "",
  });
  const [agreed, setAgreed] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const updateField = (field) => (event) => {
    setForm((current) => ({ ...current, [field]: event.target.value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (!form.name.trim() || !form.username.trim() || !form.email.trim() || !form.password) {
      setError("Fill in all required fields.");
      return;
    }

    if (!agreed) {
      setError("You need to accept the terms before creating an account.");
      return;
    }

    setLoading(true);

    try {
      const result = await signUpUser(form);
      const needsConfirmation = !result?.session;

      setSuccess(
        needsConfirmation
          ? "Account created. Check your email to confirm the account, then sign in."
          : "Account created and profile saved to Supabase."
      );
      setForm({
        name: "",
        username: "",
        email: "",
        password: "",
      });
      setAgreed(false);
      setShowPassword(false);
    } catch (signupError) {
      setError(signupError.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="auth-page signup-page">
      <div className="auth-bg-layer" />
      <div className="auth-grain" />
      <div className="auth-deco-line h l" />
      <div className="auth-deco-line h r" />

      <section className="auth-card-wrap">
        <aside className="auth-panel-left signup-panel-left">
          <div className="auth-brand-badge">
            <div className="auth-brand-icon">
              <BrandIcon />
            </div>
            <span className="auth-brand-label">SecurCoach AI</span>
          </div>

          <div className="auth-left-headline">
            <h1 className="auth-app-name">
              Create Access.
              <br />
              <span>Start</span>
              <br />
              Strong.
            </h1>
            <p className="auth-app-tagline">
              Build your profile once, then keep your training history and coaching data in sync.
            </p>
          </div>

          <p className="auth-left-footer">(C) 2025 SecurCoach AI - All rights reserved</p>
        </aside>

        <section className="auth-panel-right signup-panel-right">
          <div className="auth-form-header">
            <h2 className="auth-form-title">Create account</h2>
            <p className="auth-form-subtitle">
              Set up your credentials and save your profile to Supabase.
            </p>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="auth-field-row">
              <div className="auth-field">
                <label htmlFor="signup-name">Name</label>
                <div className="auth-input-wrap">
                  <input
                    id="signup-name"
                    className="auth-input"
                    type="text"
                    placeholder="John Doe"
                    value={form.name}
                    onChange={updateField("name")}
                  />
                  <UserIcon />
                </div>
              </div>

              <div className="auth-field">
                <label htmlFor="signup-username">Username</label>
                <div className="auth-input-wrap">
                  <input
                    id="signup-username"
                    className="auth-input"
                    type="text"
                    placeholder="johndoe"
                    value={form.username}
                    onChange={updateField("username")}
                  />
                  <AtIcon />
                </div>
              </div>
            </div>

            <div className="auth-field">
              <label htmlFor="signup-email">Email</label>
              <div className="auth-input-wrap">
                <input
                  id="signup-email"
                  className="auth-input"
                  type="email"
                  placeholder="you@example.com"
                  autoComplete="email"
                  value={form.email}
                  onChange={updateField("email")}
                />
                <EmailIcon />
              </div>
            </div>

            <div className="auth-field">
              <label htmlFor="signup-password">Password</label>
              <div className="auth-input-wrap">
                <input
                  id="signup-password"
                  className="auth-input auth-password-input"
                  type={showPassword ? "text" : "password"}
                  placeholder="********"
                  autoComplete="new-password"
                  value={form.password}
                  onChange={updateField("password")}
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

            <div className="signup-terms-row">
              <label className="auth-checkbox" htmlFor="signup-agree">
                <input
                  id="signup-agree"
                  type="checkbox"
                  checked={agreed}
                  onChange={(event) => setAgreed(event.target.checked)}
                />
                <span>I agree to the terms and privacy policy.</span>
              </label>
            </div>

            {error ? <div className="auth-message error">{error}</div> : null}
            {success ? <div className="auth-message success">{success}</div> : null}

            <button type="submit" className="auth-button" disabled={loading}>
              {loading ? "Creating account..." : "Create account"}
            </button>

            <div className="auth-divider">
              <span />
              <p>profile sync</p>
              <span />
            </div>

            <p className="auth-inline-note">
              Already have an account?{" "}
              <button type="button" className="signup-switch-link" onClick={onSwitchToLogin}>
                Sign in
              </button>
            </p>
          </form>
        </section>
      </section>
    </main>
  );
}

export default SignupLayout;

import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import "./Auth.css";
import { useLanguage } from "./language/LanguageContext";
import { LANGUAGE_BUTTON_LABELS, LANGUAGE_SEQUENCE } from "./language/languageSystem";

import { API_BASE } from "./config/api";
import { getTranslations } from "./locales";


const AUTH_ROUTES = {
  "#login": "login",
  "#signup": "signup",
  "#forgot-password": "reset",
  "#reset": "reset",
};

const routeForView = (view) => {
  if (view === "signup") return "#signup";
  if (view === "reset") return "#forgot-password";
  return "#login";
};

const resetParamsFromHash = () => {
  const [, query = ""] = window.location.hash.split("?");
  return new URLSearchParams(query);
};

const getViewFromLocation = () => {
  const hashRoute = window.location.hash.split("?")[0];
  return AUTH_ROUTES[hashRoute] || "login";
};

const isEmail = (value) => /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(value);

function Auth({ setToken }) {
  const { language, setLanguage, headers: languageHeaders } = useLanguage();
  const [view, setView] = useState(getViewFromLocation);
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [signupOtp, setSignupOtp] = useState("");
  const [signupPending, setSignupPending] = useState(false);
  const [resetEmail, setResetEmail] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [resetStep, setResetStep] = useState("email");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const t = getTranslations(language);

  const applyResetParams = useCallback(() => {
    const params = resetParamsFromHash();
    const token = params.get("token") || "";
    const emailParam = params.get("email") || "";
    if (token) {
      setResetToken(token);
      setResetEmail(emailParam);
      setResetStep("password");
      setView("reset");
      setMessage(t.auth_linkReady);
    }
  }, [t.auth_linkReady]);

  const openAuthView = (nextView, options = {}) => {
    setView(nextView);
    if (!options.keepFeedback) {
      setMessage("");
      setError("");
    }
    setPassword("");
    setConfirmPassword("");
    setSignupOtp("");
    setSignupPending(false);
    if (nextView !== "reset") {
      setResetStep("email");
      setResetToken("");
    }
    const nextHash = routeForView(nextView);
    if (window.location.hash !== nextHash) {
      window.history.pushState(null, "", nextHash);
    }
  };

  useEffect(() => {
    document.documentElement.lang = language === "hi" ? "hi" : language === "hinglish" ? "hi-IN" : "en";
  }, [language]);

  useEffect(() => {
    applyResetParams();
    const handleRouteChange = () => {
      setView(getViewFromLocation());
      setMessage("");
      setError("");
      applyResetParams();
    };
    window.addEventListener("hashchange", handleRouteChange);
    return () => window.removeEventListener("hashchange", handleRouteChange);
  }, [applyResetParams]);

  const backendError = (err) => {
    const detail = err.response?.data?.detail;
    if (Array.isArray(detail)) return detail.map((item) => item.msg).join(" ");
    return detail || t.auth_loginError;
  };

  const validateBeforeSubmit = () => {
    if (view === "login") {
      if (!email.trim()) return t.auth_requiredIdentifier;
      if (!password) return t.auth_passwordTooShort;
    }
    if (view === "signup") {
      if (signupPending) {
        if (!/^\d{6}$/.test(signupOtp.trim())) return t.auth_otpSent;
        return "";
      }
      if (!isEmail(email.trim())) return t.auth_requiredEmail;
      if (password.length < 8) return t.auth_passwordTooShort;
      if (password !== confirmPassword) return t.auth_passwordMismatch;
    }
    if (view === "reset") {
      if (!isEmail(resetEmail.trim())) return t.auth_requiredEmail;
      if (resetStep === "password") {
        if (password.length < 8) return t.auth_passwordTooShort;
        if (password !== confirmPassword) return t.auth_passwordMismatch;
      }
    }
    return "";
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");

    const validationError = validateBeforeSubmit();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    try {
      if (view === "login") {
        const res = await axios.post(`${API_BASE}/login`, {
          email: email.trim(),
          password,
        });
        const accessToken = res.data.access_token;
        localStorage.setItem("token", accessToken);
        window.history.replaceState(null, "", window.location.pathname);
        setToken(accessToken);
        axios.post(
          `${API_BASE}/api/language/user`,
          { language },
          { headers: { ...languageHeaders, Authorization: `Bearer ${accessToken}` } }
        ).catch((languageError) => {
          console.error(languageError);
        });
      } else if (view === "signup") {
        if (signupPending) {
          const res = await axios.post(`${API_BASE}/verify-signup-otp`, {
            email: email.trim(),
            otp: signupOtp.trim(),
          });
          openAuthView("login", { keepFeedback: true });
          setMessage(res.data?.message || t.auth_signupSuccess);
          return;
        }
        const payload = {
          email: email.trim(),
          password,
        };
        if (username.trim()) payload.username = username.trim();
        const res = await axios.post(`${API_BASE}/signup`, payload);
        if (res.data?.requires_otp) {
          setSignupPending(true);
          setMessage(res.data?.dev_otp ? `${res.data.message} OTP: ${res.data.dev_otp}` : (res.data?.message || t.auth_otpSent));
        } else {
          openAuthView("login", { keepFeedback: true });
          setMessage(res.data?.message || t.auth_signupSuccess);
        }
      } else if (view === "reset" && resetStep === "email") {
        const res = await axios.post(`${API_BASE}/forgot-password`, {
          email: resetEmail.trim(),
        });
        setMessage(res.data?.dev_reset_url ? `${res.data.message} ${res.data.dev_reset_url}` : res.data.message);
      } else if (view === "reset" && resetStep === "password") {
        await axios.post(`${API_BASE}/reset-password`, {
          email: resetEmail.trim(),
          token: resetToken,
          new_password: password,
        });
        openAuthView("login", { keepFeedback: true });
        setMessage(t.auth_resetSuccess);
        setEmail(resetEmail);
        setResetEmail("");
        setResetToken("");
        setResetStep("email");
      }
    } catch (err) {
      setError(backendError(err));
    } finally {
      setLoading(false);
    }
  };

  const submitLabel = () => {
    if (loading) return t.auth_pleaseWait;
    if (view === "login") return t.auth_login;
    if (view === "signup") return signupPending ? t.auth_verifyOtp : t.auth_signup;
    if (view === "reset" && resetStep === "email") return t.auth_sendReset;
    return t.auth_resetPasswordConfirm;
  };

  return (
    <div className="auth-container">
      <div className="auth-language">
        <button
          className="ghost-btn"
          onClick={() => {
            const currentIndex = LANGUAGE_SEQUENCE.indexOf(language);
            setLanguage(LANGUAGE_SEQUENCE[(currentIndex + 1) % LANGUAGE_SEQUENCE.length]);
          }}
        >
          {LANGUAGE_BUTTON_LABELS[language] || LANGUAGE_BUTTON_LABELS.en}
        </button>
      </div>

      <div className="auth-card">
        <div className="auth-brand">
          <div className="auth-logo">DM</div>
          <div>
            <p className="auth-tag">{t.auth_dataMantri}</p>
            <p className="auth-subtitle">{t.auth_subtitle}</p>
          </div>
        </div>

        <h1 className="auth-title">
          {view === "login" && t.auth_welcomeBack}
          {view === "signup" && t.auth_createAccount}
          {view === "reset" && t.auth_resetPassword}
        </h1>

        {view === "reset" && resetStep === "email" && <p className="auth-help">{t.auth_resetInstructions}</p>}

        <form className="auth-form" onSubmit={handleSubmit}>
          {view === "signup" && !signupPending && (
            <input
              type="text"
              placeholder={t.auth_username}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="auth-input"
              autoComplete="username"
            />
          )}

          <input
            type={view === "login" ? "text" : "email"}
            placeholder={view === "login" ? t.auth_emailOrUsername : t.auth_email}
            value={view === "reset" ? resetEmail : email}
            onChange={(e) => (view === "reset" ? setResetEmail(e.target.value) : setEmail(e.target.value))}
            className="auth-input"
            autoComplete={view === "login" ? "username" : "email"}
            required
          />

          {(view === "login" || (view === "signup" && !signupPending) || (view === "reset" && resetStep === "password")) && (
            <input
              type="password"
              placeholder={view === "reset" ? t.auth_resetPassword : t.auth_password}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="auth-input"
              autoComplete={view === "signup" ? "new-password" : "current-password"}
              required
            />
          )}

          {view === "signup" && signupPending && (
            <input
              type="text"
              placeholder={t.auth_otp}
              value={signupOtp}
              onChange={(e) => setSignupOtp(e.target.value)}
              className="auth-input"
              inputMode="numeric"
              maxLength={6}
              required
            />
          )}

          {((view === "signup" && !signupPending) || (view === "reset" && resetStep === "password")) && (
            <input
              type="password"
              placeholder={t.auth_confirmPassword}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="auth-input"
              autoComplete="new-password"
              required
            />
          )}

          <button type="submit" className="auth-button" disabled={loading}>
            {submitLabel()}
          </button>
        </form>

        {message && <div className="auth-message">{message}</div>}
        {error && <div className="auth-error">{error}</div>}

        <div className="auth-actions">
          {view === "login" && (
            <>
              <button type="button" className="auth-link" onClick={() => openAuthView("signup")}>{t.auth_createAccount}</button>
              <button type="button" className="auth-link" onClick={() => openAuthView("reset")}>{t.auth_forgotPassword}</button>
            </>
          )}
          {view === "signup" && (
            <button type="button" className="auth-link" onClick={() => openAuthView("login")}>{t.auth_alreadyHaveAccount}</button>
          )}
          {view === "reset" && (
            <button type="button" className="auth-link" onClick={() => openAuthView("login")}>{t.auth_backToLogin}</button>
          )}
        </div>
      </div>
    </div>
  );
}

export default Auth;

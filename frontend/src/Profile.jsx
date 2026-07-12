import React, { useCallback, useEffect, useState } from "react";
import axios from "axios";
import { API_BASE } from "./config/api";
import { getTranslations } from "./locales";


const pt = (text, language) => {
  if (language === "en") return text;
  const direct = getTranslations(language).profilePhrases?.[text];
  if (direct) return direct;
  if (language === "hi") {
    return String(text)
      .replace(/(\d+) insights,\s*(\d+) recommendations/gi, "$1 इनसाइट्स, $2 सुझाव")
      .replace(/Cleaned data: removed (\d+) duplicates, filled (\d+) missing values/gi, "क्लीन डेटा: $1 डुप्लिकेट हटे, $2 मिसिंग वैल्यू भरी गईं");
  }
  if (language === "hinglish") {
    return String(text)
      .replace(/(\d+) insights,\s*(\d+) recommendations/gi, "$1 insights, $2 recommendations")
      .replace(/Cleaned data: removed (\d+) duplicates, filled (\d+) missing values/gi, "Clean data: $1 duplicates remove hue, $2 missing values fill hui");
  }
  return text;
};

const ProfileCard = ({ userInitial, userName, userEmail, userPlan, tr }) => (
  <div className="profile-header-card">
    <div className="profile-header-info">
      <div className="profile-avatar-large">{userInitial}</div>
      <div>
        <p className="profile-label">{tr("Account owner")}</p>
        <h2>{userName}</h2>
        <p className="profile-email">{userEmail || tr("No email available")}</p>
      </div>
    </div>
    <span className="status-pill">{userPlan}</span>
  </div>
);

const StatsCard = ({ label, value, detail }) => (
  <div className="stats-card">
    <span className="stats-title">{label}</span>
    <strong>{value}</strong>
    {detail && <p className="stats-detail">{detail}</p>}
  </div>
);

const ActivityList = ({ items, tr }) => (
  <div className="activity-list-card">
    <div className="section-header profile-section-header">
      <div>
        <h3>{tr("Activity history")}</h3>
        <span>{tr("Recent datasets uploaded and reports generated.")}</span>
      </div>
    </div>
    <div className="activity-items">
      {items.length ? (
        items.map((item) => (
          <div className="activity-item" key={item.id || `${item.filename}-${item.created_at}`}>
            <div>
              <p className="activity-label">{item.filename || item.summary || tr("Recent activity")}</p>
              <span className="activity-meta">{item.summary ? tr(item.summary) : tr("Dataset uploaded")}</span>
            </div>
            <time>{new Date(item.created_at).toLocaleString()}</time>
          </div>
        ))
      ) : (
        <div className="empty-card">{tr("No recent activity captured yet.")}</div>
      )}
    </div>
  </div>
);

const SettingsToggle = ({ label, description, active, onToggle }) => (
  <button type="button" className={`settings-toggle ${active ? "active" : ""}`} onClick={onToggle}>
    <div>
      <span>{label}</span>
      <p>{description}</p>
    </div>
    <div className={`toggle-pill ${active ? "active" : ""}`}>
      <span />
    </div>
  </button>
);

const Profile = ({
  profile,
  history,
  darkMode,
  setDarkMode,
  mode,
  setMode,
  handleLogout,
  userName,
  userEmail,
  userPlan,
  plan,
  onUpgrade,
  language = "en",
}) => {
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [supportSubject, setSupportSubject] = useState("");
  const [supportMessage, setSupportMessage] = useState("");
  const [supportTickets, setSupportTickets] = useState([]);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [showTicketModal, setShowTicketModal] = useState(false);
  const [supportSubmitting, setSupportSubmitting] = useState(false);
  const [profileMessage, setProfileMessage] = useState("");
  const [profileError, setProfileError] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [adminUsers, setAdminUsers] = useState([]);
  const [adminTickets, setAdminTickets] = useState([]);
  const token = localStorage.getItem("token");
  const tr = useCallback((text) => pt(text, language), [language]);

  const usageAnalytics = [
    { label: tr("Total uploads"), value: profile?.total_uploads ?? 0 },
    { label: tr("Insights generated"), value: profile?.total_insights ?? 0 },
    { label: tr("Chatbot queries"), value: profile?.total_queries ?? 0 },
    { label: tr("Last active"), value: profile?.last_active || tr("Today") },
  ];

  const usageFor = (feature) => profile?.usage?.[feature] || profile?.limits?.[feature] || {};
  const formatUsage = (usage) => usage.unlimited ? `${usage.used || 0} / ${tr("Unlimited")}` : `${usage.used || 0} / ${usage.limit ?? 0}`;

  const recentActivity = history.slice(0, 5);

  const getAuthHeaders = useCallback(() => ({ headers: { Authorization: `Bearer ${token}` } }), [token]);

  const fetchSupportTickets = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE}/support/my`, getAuthHeaders());
      setSupportTickets(response.data.tickets || []);
    } catch (err) {
      console.error(err);
    }
  }, [getAuthHeaders]);

  const fetchAdminData = useCallback(async () => {
    if (!profile?.is_admin) return;
    try {
      const [usersResponse, ticketsResponse] = await Promise.all([
        axios.get(`${API_BASE}/admin/users`, getAuthHeaders()),
        axios.get(`${API_BASE}/admin/support`, getAuthHeaders()),
      ]);
      setAdminUsers(usersResponse.data.users || []);
      setAdminTickets(ticketsResponse.data.tickets || []);
    } catch (err) {
      console.error(err);
    }
  }, [getAuthHeaders, profile?.is_admin]);

  useEffect(() => {
    if (!token) return;
    fetchSupportTickets();
    fetchAdminData();
  }, [token, profile?.is_admin, fetchSupportTickets, fetchAdminData]);

  const submitSupportTicket = async () => {
    setProfileError("");
    setProfileMessage("");
    setSupportSubmitting(true);
    try {
      const response = await axios.post(
        `${API_BASE}/support`,
        { subject: supportSubject, message: supportMessage },
        getAuthHeaders()
      );
      setSupportSubject("");
      setSupportMessage("");
      const supportEmail = response.data.support_email;

      // Show success message immediately — don't wait for ticket/admin fetches
      setProfileMessage(
        language === "hi"
          ? `सपोर्ट अनुरोध जमा हुआ और ${supportEmail} पर ईमेल सफलतापूर्वक भेजा गया.`
          : language === "hinglish"
          ? `Support request submit ho gaya aur ${supportEmail} par email successfully send hua.`
          : `Support request submitted and email sent successfully to ${supportEmail}.`
      );

      // Refresh lists in background so UI shows success without delay
      fetchSupportTickets();
      fetchAdminData();
    } catch (err) {
      setProfileError(err.response?.data?.detail || tr("Could not submit support request."));
      // Refresh lists in background even on error
      fetchSupportTickets();
      fetchAdminData();
    } finally {
      setSupportSubmitting(false);
    }
  };

  const changePassword = async () => {
    setProfileError("");
    setProfileMessage("");
    try {
      await axios.post(
        `${API_BASE}/change-password`,
        { current_password: currentPassword, new_password: newPassword },
        getAuthHeaders()
      );
      setCurrentPassword("");
      setNewPassword("");
      setProfileMessage(tr("Password changed successfully."));
    } catch (err) {
      setProfileError(err.response?.data?.detail || tr("Could not change password."));
    }
  };

  return (
    <div className="profile-page">
      <div className="profile-top-grid">
        <div className="profile-card-large panel-card">
          <ProfileCard userInitial={userName?.charAt(0).toUpperCase() || "D"} userName={userName} userEmail={userEmail} userPlan={userPlan} tr={tr} />
          <div className="profile-welcome-copy">
            <h3>{tr("Manage your account and subscription")}</h3>
            <p>{tr("Keep your workspace settings, usage, and security controls in one polished, premium dashboard.")}</p>
          </div>
        </div>

        <div className="subscription-card panel-card">
          <div className="section-header profile-section-header">
            <div>
              <h3>{tr("Subscription")}</h3>
              <span>{tr("Current plan details")}</span>
            </div>
          </div>
          <div className="subscription-details">
            <div className="subscription-line">
              <span>{tr("Plan")}</span>
              <strong>{userPlan}</strong>
            </div>
            <div className="subscription-line">
              <span>{tr("Dataset uploads")}</span>
              <strong>{formatUsage(usageFor("csv_upload"))}</strong>
            </div>
            <div className="subscription-line">
              <span>{tr("AI queries")}</span>
              <strong>{formatUsage(usageFor("chatbot_query"))}</strong>
            </div>
            <div className="subscription-line">
              <span>{tr("Mitra voice")}</span>
              <strong>{formatUsage(usageFor("voice_advisor"))}</strong>
            </div>
            <div className="subscription-line">
              <span>{tr("Renewal")}</span>
              <strong>{tr(profile?.subscription?.renewal || "Monthly")}</strong>
            </div>
            {profile?.trial_days_remaining != null && (
              <div className="subscription-line">
                <span>{tr("Trial ends")}</span>
                <strong>{profile.trial_days_remaining} {tr("days")}</strong>
              </div>
            )}
            {profile?.subscription_days_remaining != null && (
              <div className="subscription-line">
                <span>{tr("Premium renews")}</span>
                <strong>{profile.subscription_days_remaining} {tr("days")}</strong>
              </div>
            )}
          </div>
          <button className="primary-btn" onClick={onUpgrade}>
            {plan === "premium" ? tr("Manage plan") : tr("Upgrade plan")}
          </button>
        </div>
      </div>

      <div className="usage-grid">
        {["csv_upload", "chatbot_query", "voice_advisor", "report_download"].map((feature) => {
          const usage = usageFor(feature);
          return (
            <StatsCard
              key={feature}
              label={usage.label ? tr(usage.label) : feature.replace(/_/g, " ")}
              value={usage.unlimited ? tr("Unlimited") : `${usage.remaining ?? 0} ${tr("left")}`}
              detail={usage.unlimited ? tr("Premium access") : `${usage.used || 0}/${usage.limit || 0} ${tr("used this")} ${tr(usage.period || "period")}`}
            />
          );
        })}
      </div>

      <div className="usage-grid">
        {usageAnalytics.map((item) => (
          <StatsCard key={item.label} label={item.label} value={item.value} />
        ))}
      </div>

      {!!profile?.billing_history?.length && (
        <div className="activity-list-card panel-card">
          <div className="section-header profile-section-header">
            <div>
              <h3>{tr("Billing history")}</h3>
              <span>{tr("Payments and subscription activity")}</span>
            </div>
          </div>
          <div className="activity-items">
            {profile.billing_history.slice(0, 5).map((item) => (
              <div className="activity-item" key={item.id}>
                <div>
                  <p className="activity-label">{item.plan_code} · {item.interval}</p>
                  <span className="activity-meta">{item.status} · ₹{item.amount}</span>
                </div>
                <time>{new Date(item.created_at).toLocaleString()}</time>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="profile-bottom-grid">
        <ActivityList items={recentActivity} tr={tr} />

        <div className="settings-security-grid">
          <div className="settings-panel panel-card">
            <div className="section-header profile-section-header">
            <div>
                <h3>{tr("Settings")}</h3>
                <span>{tr("Quick access toggles")}</span>
              </div>
            </div>
            <div className="settings-list">
              <SettingsToggle
                label={tr("Dark mode")}
                description={tr("Switch the application theme.")}
                active={darkMode}
                onToggle={() => setDarkMode(!darkMode)}
              />
              <SettingsToggle
                label={tr("Business mode")}
                description={tr("Set your dashboard for executive insights.")}
                active={mode === "business"}
                onToggle={() => setMode("business")}
              />
              <SettingsToggle
                label={tr("Data mode")}
                description={tr("Switch to analyst-ready detail.")}
                active={mode === "data"}
                onToggle={() => setMode("data")}
              />
              <SettingsToggle
                label={tr("Notifications")}
                description={tr("Receive email alerts and updates.")}
                active={notificationsEnabled}
                onToggle={() => setNotificationsEnabled((value) => !value)}
              />
            </div>
          </div>

          <div className="security-panel panel-card">
            <div className="section-header profile-section-header">
              <div>
                <h3>{tr("Security")}</h3>
                <span>{tr("Account-level controls")}</span>
              </div>
            </div>
            <div className="security-actions">
              <input
                className="search-input"
                type="password"
                placeholder={tr("Current password")}
                value={currentPassword}
                onChange={(event) => setCurrentPassword(event.target.value)}
              />
              <input
                className="search-input"
                type="password"
                placeholder={tr("New password")}
                value={newPassword}
                onChange={(event) => setNewPassword(event.target.value)}
              />
              <button className="secondary-btn" onClick={changePassword} disabled={!currentPassword || !newPassword}>{tr("Change password")}</button>
              <button className="secondary-btn" onClick={handleLogout}>{tr("Logout")}</button>
            </div>
          </div>
        </div>

          {showTicketModal && selectedTicket && (
            <div
              className="modal-overlay"
              role="dialog"
              aria-modal="true"
              aria-label={selectedTicket.subject || "Support ticket details"}
              onClick={() => { setShowTicketModal(false); setSelectedTicket(null); }}
            >
              <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <button className="modal-close" aria-label="Close" onClick={() => { setShowTicketModal(false); setSelectedTicket(null); }}>×</button>
                <div className="modal-header">
                  <h3>{selectedTicket.subject}</h3>
                  <div className="modal-meta">{selectedTicket.user_email ? `${selectedTicket.user_email} · ` : ''}{new Date(selectedTicket.created_at).toLocaleString()}</div>
                </div>
                <div className="modal-body">
                  <p className="ticket-full-message">{selectedTicket.message}</p>
                  {selectedTicket.response && (
                    <div className="ticket-response">
                      <h4>Response</h4>
                      <div>{selectedTicket.response}</div>
                    </div>
                  )}
                </div>
                <div className="modal-actions">
                  <button className="secondary-btn" onClick={() => { setShowTicketModal(false); setSelectedTicket(null); }}>Close</button>
                </div>
              </div>
            </div>
          )}
      </div>

      <div className="profile-bottom-grid">
        <div className="support-panel panel-card">
          <div className="section-header profile-section-header">
            <div>
              <h3>{tr("User support")}</h3>
              <span>{tr("Ask for help with uploads, analysis, billing, or account access.")}</span>
            </div>
          </div>
          <div className="support-form">
            <input
              className="search-input"
              placeholder={tr("Subject")}
              value={supportSubject}
              onChange={(event) => setSupportSubject(event.target.value)}
            />
            <textarea
              className="support-textarea"
              placeholder={tr("How can we help?")}
              value={supportMessage}
              onChange={(event) => setSupportMessage(event.target.value)}
            />
            <button className="primary-btn" onClick={submitSupportTicket} disabled={!supportSubject || !supportMessage || supportSubmitting}>
              {supportSubmitting ? tr("Submitting...") : tr("Submit request")}
            </button>
          </div>
          {profileMessage && <div className="auth-message">{profileMessage}</div>}
          {profileError && <div className="upload-error">{profileError}</div>}
        </div>

        <div className="activity-list-card">
          <div className="section-header profile-section-header">
            <div>
              <h3>{tr("My support tickets")}</h3>
              <span>{tr("Track requests you have submitted.")}</span>
            </div>
          </div>
          <div className="activity-items support-ticket-list">
            {supportTickets.length ? supportTickets.map((ticket) => (
              <div className="activity-item support-ticket" key={ticket.id}>
                <div className="ticket-main">
                  <p className="activity-label">{ticket.subject}</p>
                  <span className="activity-meta">{new Date(ticket.created_at).toLocaleString()}</span>
                  <div className="ticket-excerpt">{ticket.message}</div>
                </div>
                <div className="ticket-actions">
                  <button className="secondary-btn" onClick={() => { setSelectedTicket(ticket); setShowTicketModal(true); }}>Open</button>
                </div>
              </div>
            )) : <div className="empty-card">{tr("No support tickets yet.")}</div>}
          </div>
        </div>
      </div>

      {profile?.is_admin && (
        <div className="profile-bottom-grid">
          <div className="activity-list-card">
            <div className="section-header profile-section-header">
              <div>
                <h3>{tr("Admin users")}</h3>
                <span>{tr("Users, plans, uploads, and query usage stored in the app database.")}</span>
              </div>
            </div>
            <div className="activity-items">
              {adminUsers.map((user) => (
                <div className="activity-item" key={user.id}>
                  <div>
                    <p className="activity-label">{user.email}</p>
                    <span className="activity-meta">{user.total_uploads} {tr("uploads")} · {user.total_queries} {tr("queries")}</span>
                  </div>
                  <span className="status-pill">{user.plan}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="activity-list-card">
            <div className="section-header profile-section-header">
              <div>
                <h3>{tr("Admin support inbox")}</h3>
                <span>{tr("All user support requests.")}</span>
              </div>
            </div>
            <div className="activity-items">
              {adminTickets.map((ticket) => (
                <div className="activity-item" key={ticket.id}>
                  <div>
                    <p className="activity-label">{ticket.subject}</p>
                    <span className="activity-meta">{ticket.user_email} · {ticket.status}</span>
                  </div>
                  <time>{new Date(ticket.created_at).toLocaleString()}</time>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Profile;
 
// Ticket modal rendering placed at file end to keep Profile component file-scoped state

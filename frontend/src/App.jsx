import { useState } from "react";
import "./App.css";

const API = "http://127.0.0.1:5000/api";

const EMPTY_FORM = {
  credentialId: "",
  candidateName: "",
  credentialName: "",
  issuerName: "",
};

function App() {
  const [activeTab, setActiveTab] = useState("verify");
  const [credentialId, setCredentialId] = useState("");
  const [verifyFile, setVerifyFile] = useState(null);
  const [issueFile, setIssueFile] = useState(null);
  const [fileInputKey, setFileInputKey] = useState(0);
  const [result, setResult] = useState(null);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [dashboard, setDashboard] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);

  async function readResponse(response) {
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(
        data.error || data.message || "The request failed."
      );
    }

    return data;
  }

  async function loadDashboard() {
    setLoading(true);
    setMessage("");

    try {
      const response = await fetch(`${API}/dashboard`);
      const data = await readResponse(response);
      setDashboard(data);
    } catch (error) {
      setMessage(
        error.message || "Could not connect to the backend."
      );
    } finally {
      setLoading(false);
    }
  }

  function changeTab(tab) {
    setActiveTab(tab);
    setMessage("");
    setResult(null);

    if (tab === "dashboard") {
      loadDashboard();
    }
  }

  async function verifyCredential(event) {
    event.preventDefault();
    setLoading(true);
    setResult(null);
    setMessage("");

    try {
      if (!credentialId.trim()) {
        throw new Error("Please enter a credential ID.");
      }

      if (!verifyFile) {
        throw new Error("Please upload the original PDF document.");
      }

      const encodedId = encodeURIComponent(credentialId.trim());

      // Retrieve credential details from the blockchain.
      const detailsResponse = await fetch(
        `${API}/credentials/${encodedId}`
      );

      const details = await readResponse(detailsResponse);

      // Send the uploaded PDF to compare its SHA-256 hash.
      const documentData = new FormData();
      documentData.append("document", verifyFile);

      const verifyResponse = await fetch(
        `${API}/credentials/${encodedId}/verify-document`,
        {
          method: "POST",
          body: documentData,
        }
      );

      const verification = await readResponse(verifyResponse);

      setResult({
        ...details,
        ...verification,
      });

      setMessage(verification.message);
    } catch (error) {
      setMessage(
        error.message || "Could not connect to the backend."
      );
    } finally {
      setLoading(false);
    }
  }

  async function issueCredential(event) {
    event.preventDefault();
    setLoading(true);
    setResult(null);
    setMessage("");

    try {
      if (!issueFile) {
        throw new Error("Please upload the credential PDF.");
      }

      const formData = new FormData();

      Object.entries(form).forEach(([key, value]) => {
        formData.append(key, value.trim());
      });

      formData.append("document", issueFile);

      const response = await fetch(
        `${API}/credentials/with-document`,
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await readResponse(response);

      setMessage(
        `Credential issued successfully. SHA-256: ${data.credentialHash}. Transaction: ${data.transactionHash}`
      );

      setCredentialId(data.credentialId);
      setForm(EMPTY_FORM);
      setIssueFile(null);
      setFileInputKey((key) => key + 1);
    } catch (error) {
      setMessage(
        error.message || "Could not connect to the backend."
      );
    } finally {
      setLoading(false);
    }
  }

  async function revokeCredential() {
    if (!result?.credentialId || !result.isValid) {
      return;
    }

    const confirmed = window.confirm(
      `Are you sure you want to revoke credential ${result.credentialId}?`
    );

    if (!confirmed) {
      return;
    }

    setLoading(true);
    setMessage("");

    try {
      const response = await fetch(
        `${API}/credentials/${encodeURIComponent(
          result.credentialId
        )}/revoke`,
        {
          method: "POST",
        }
      );

      const data = await readResponse(response);

      setMessage(
        `Credential revoked successfully. Transaction: ${data.transactionHash}`
      );

      setResult((previous) => ({
        ...previous,
        isValid: false,
        credentialValid: false,
        verificationSuccessful: false,
        message: "Credential has been revoked.",
      }));
    } catch (error) {
      setMessage(
        error.message || "Could not connect to the backend."
      );
    } finally {
      setLoading(false);
    }
  }

  function formatDate(value) {
    if (!value) {
      return "Date unavailable";
    }

    const date = new Date(value);

    return Number.isNaN(date.getTime())
      ? "Date unavailable"
      : date.toLocaleString();
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a
          className="brand"
          href="#"
          onClick={(event) => event.preventDefault()}
        >
          <span className="brand-mark">H</span>
          HireProof
        </a>

        <span className="network-label">
          <span className="status-dot" />
          Local blockchain
        </span>
      </header>

      <main className="main-content">
        <section className="hero">
          <p className="eyebrow">TRUST · VERIFY · HIRE</p>

          <h1>
            Credentials you can <span>trust.</span>
          </h1>

          <p className="hero-description">
            Verify academic and professional credentials with
            blockchain-backed records and document integrity checks.
          </p>
        </section>

        <section className="workspace">
          <div className="tabs">
            <button
              type="button"
              className={
                activeTab === "verify" ? "tab active" : "tab"
              }
              onClick={() => changeTab("verify")}
            >
              Verify credential
            </button>

            <button
              type="button"
              className={
                activeTab === "dashboard" ? "tab active" : "tab"
              }
              onClick={() => changeTab("dashboard")}
            >
              Dashboard
            </button>

            <button
              type="button"
              className={
                activeTab === "issue" ? "tab active" : "tab"
              }
              onClick={() => changeTab("issue")}
            >
              Issue credential
            </button>
          </div>

          {activeTab === "dashboard" ? (
            <div className="panel dashboard-panel">
              <div>
                <h2>HireProof Dashboard</h2>
                <p className="muted">
                  Overview of credential activity tracked by this
                  application.
                </p>
              </div>

              <button
                type="button"
                className="secondary-button refresh-button"
                disabled={loading}
                onClick={loadDashboard}
              >
                {loading ? "Refreshing..." : "Refresh dashboard"}
              </button>

              {dashboard && (
                <>
                  <div className="stats-grid">
                    <div className="stat-card">
                      <span>Credentials issued</span>
                      <strong>{dashboard.totalIssued}</strong>
                    </div>

                    <div className="stat-card">
                      <span>Credentials revoked</span>
                      <strong>{dashboard.totalRevoked}</strong>
                    </div>

                    <div className="stat-card">
                      <span>Active (tracked)</span>
                      <strong>{dashboard.activeCredentials}</strong>
                    </div>
                  </div>

                  <div className="history-section">
                    <h3>Recent transactions</h3>

                    {dashboard.recentTransactions.length === 0 ? (
                      <p className="muted">
                        No activity tracked yet. Issue a new
                        credential to get started.
                      </p>
                    ) : (
                      <div className="transaction-list">
                        {dashboard.recentTransactions.map(
                          (item, index) => (
                            <div
                              className="transaction-item"
                              key={`${
                                item.transactionHash ||
                                item.credentialId
                              }-${index}`}
                            >
                              <div className="transaction-top">
                                <strong>{item.type}</strong>

                                <span
                                  className={
                                    item.type === "Credential Issued"
                                      ? "pill valid"
                                      : "pill revoked"
                                  }
                                >
                                  {item.type === "Credential Issued"
                                    ? "Issued"
                                    : "Revoked"}
                                </span>
                              </div>

                              <p>
                                Credential ID:{" "}
                                <strong>
                                  {item.credentialId || "—"}
                                </strong>
                              </p>

                              {item.candidateName && (
                                <p>
                                  Candidate:{" "}
                                  <strong>{item.candidateName}</strong>
                                </p>
                              )}

                              <p className="transaction-date">
                                {formatDate(item.timestamp)}
                              </p>

                              <p className="transaction-hash">
                                <span>Transaction hash</span>
                                <code>
                                  {item.transactionHash || "Unavailable"}
                                </code>
                              </p>
                            </div>
                          )
                        )}
                      </div>
                    )}
                  </div>
                </>
              )}

              {message && (
                <p className="message" role="status">
                  {message}
                </p>
              )}
            </div>
          ) : activeTab === "verify" ? (
            <form className="panel" onSubmit={verifyCredential}>
              <div>
                <h2>Verify a credential</h2>
                <p className="muted">
                  Enter the credential ID and upload the original PDF
                  to check its integrity and current status.
                </p>
              </div>

              <div className="field">
                <label htmlFor="verifyId">Credential ID</label>
                <input
                  id="verifyId"
                  value={credentialId}
                  onChange={(event) =>
                    setCredentialId(event.target.value)
                  }
                  placeholder="e.g. HP007"
                  required
                />
              </div>

              <div className="field">
                <label htmlFor="verifyDocument">
                  Original credential PDF
                </label>

                <input
                  id="verifyDocument"
                  type="file"
                  accept=".pdf,application/pdf"
                  onChange={(event) =>
                    setVerifyFile(event.target.files?.[0] || null)
                  }
                  required
                />

                <p className="field-hint">
                  Upload the same PDF that was used when issuing the
                  credential.
                </p>
              </div>

              <button className="primary-button" disabled={loading}>
                {loading
                  ? "Verifying document..."
                  : "Verify document →"}
              </button>

              {result && (
                <div className="result-card">
                  <div className="result-heading">
                    <h3>Verification results</h3>

                    <span
                      className={
                        result.verificationSuccessful
                          ? "pill valid"
                          : "pill revoked"
                      }
                    >
                      {result.verificationSuccessful
                        ? "Verified"
                        : !result.isValid ||
                            result.credentialValid === false
                          ? "Revoked / Invalid"
                          : "Not verified"}
                    </span>
                  </div>

                  <div className="details">
                    <p>
                      <span>Candidate</span>
                      <strong>{result.candidateName}</strong>
                    </p>

                    <p>
                      <span>Credential</span>
                      <strong>{result.credentialName}</strong>
                    </p>

                    <p>
                      <span>Issuer</span>
                      <strong>{result.issuerName}</strong>
                    </p>

                    <p>
                      <span>Credential ID</span>
                      <strong>{result.credentialId}</strong>
                    </p>

                    <p>
                      <span>Issue date</span>
                      <strong>
                        {formatDate(Number(result.issueDate) * 1000)}
                      </strong>
                    </p>

                    <p>
                      <span>Document integrity</span>
                      <strong
                        className={
                          result.documentMatches
                            ? "text-success"
                            : "text-error"
                        }
                      >
                        {result.documentMatches
                          ? "PDF matches the stored hash"
                          : "PDF does not match the stored hash"}
                      </strong>
                    </p>

                    <p>
                      <span>Credential status</span>
                      <strong>
                        {result.isValid && result.credentialValid
                          ? "Active"
                          : "Revoked"}
                      </strong>
                    </p>

                    <p>
                      <span>Stored SHA-256 hash</span>
                      <strong className="hash">
                        {result.credentialHash}
                      </strong>
                    </p>
                  </div>

                  {result.isValid && (
                    <button
                      type="button"
                      className="secondary-button"
                      disabled={loading}
                      onClick={revokeCredential}
                    >
                      Revoke credential
                    </button>
                  )}
                </div>
              )}

              {message && (
                <p className="message" role="status">
                  {message}
                </p>
              )}
            </form>
          ) : (
            <form className="panel" onSubmit={issueCredential}>
              <div>
                <h2>Issue a credential</h2>
                <p className="muted">
                  Register a credential and store its PDF's SHA-256
                  hash on the local blockchain.
                </p>
              </div>

              {[
                ["credentialId", "Credential ID", "e.g. HP008"],
                ["candidateName", "Candidate name", "Full name"],
                ["credentialName", "Credential name", "e.g. B.Tech CSE"],
                ["issuerName", "Issuing institution", "Institution name"],
              ].map(([name, label, placeholder]) => (
                <div className="field" key={name}>
                  <label htmlFor={name}>{label}</label>

                  <input
                    id={name}
                    value={form[name]}
                    onChange={(event) =>
                      setForm((previous) => ({
                        ...previous,
                        [name]: event.target.value,
                      }))
                    }
                    placeholder={placeholder}
                    required
                  />
                </div>
              ))}

              <div className="field">
                <label htmlFor="issueDocument">Credential PDF</label>

                <input
                  key={fileInputKey}
                  id="issueDocument"
                  type="file"
                  accept=".pdf,application/pdf"
                  onChange={(event) =>
                    setIssueFile(event.target.files?.[0] || null)
                  }
                  required
                />

                <p className="field-hint">
                  The PDF is hashed automatically. Only its SHA-256
                  hash is recorded on the blockchain by this workflow.
                </p>
              </div>

              <button className="primary-button" disabled={loading}>
                {loading
                  ? "Issuing credential..."
                  : "Issue credential →"}
              </button>

              {message && (
                <p className="message" role="status">
                  {message}
                </p>
              )}
            </form>
          )}
        </section>

        <p className="disclaimer">
          HireProof demo · Connected to a local development blockchain.
          Do not enter real personal or confidential data.
        </p>
      </main>
    </div>
  );
}

export default App;
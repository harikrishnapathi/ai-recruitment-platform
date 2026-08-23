// =====================================================
// APP
// =====================================================
import { useEffect, useMemo, useState } from "react";
import api from "./api";

function App() {
  const [token, setToken] = useState(
    localStorage.getItem("access_token")
  );
  const [accountType, setAccountType] = useState(
    localStorage.getItem("account_type")
  );

  function handleLogin(accessToken, type) {
    localStorage.setItem("access_token", accessToken);
    localStorage.setItem("account_type", type);
    setToken(accessToken);
    setAccountType(type);
  }

  function handleLogout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("organization_id");
    localStorage.removeItem("account_type");
    setToken(null);
    setAccountType(null);
  }

  if (!token) {
    return <Login onLogin={handleLogin} />;
  }

  if (accountType === "CANDIDATE") {
    return <CandidateDashboard onLogout={handleLogout} />;
  }

  return <Dashboard onLogout={handleLogout} />;
}

// =====================================================
// LOGIN / REGISTRATION
// =====================================================

function Login({ onLogin }) {
  const [mode, setMode] = useState("login");
  const [accountType, setAccountType] = useState("RECRUITER");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
    if (mode === "register") {
  await api.post("/auth/register", {
    email,
    password,
    first_name: firstName,
    last_name: lastName,
    role: accountType === "CANDIDATE" ? "candidate" : "recruiter",
  });
}
     const response = await api.post("/auth/login", {
  email,
  password,
});

const accessToken = response.data.access_token;
const organizationId = response.data.organization_id;

if (!accessToken) {
  throw new Error("Login succeeded but no access token was returned.");
}

if (organizationId) {
  localStorage.setItem(
    "organization_id",
    organizationId
  );
} else {
  localStorage.removeItem("organization_id");
}

// Determine account type from the JWT/user profile.
// Candidate and recruiter accounts are handled separately.
let type = accountType;

try {
  const payload = JSON.parse(
    atob(accessToken.split(".")[1])
  );

  if (payload.role === "candidate") {
    type = "CANDIDATE";
  } else if (
    payload.role === "recruiter" ||
    payload.role === "employer"
  ) {
    type = "RECRUITER";
  }
} catch (jwtError) {
  console.error("Could not decode login token:", jwtError);
}

if (!type) {
  throw new Error(
    "Login succeeded, but the account type could not be determined."
  );
}

onLogin(accessToken, type);
    } catch (error) {
      console.error(
        "Authentication error:",
        error.response?.data || error
      );

      const detail = error.response?.data?.detail;

      if (typeof detail === "string") {
        setError(detail);
      } else if (Array.isArray(detail)) {
        setError(
          detail.map((item) => item.msg).join(", ")
        );
      } else {
        setError(
          "Authentication failed. Please check your details."
        );
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="auth-badge">
          AI Recruitment & Talent Intelligence
        </div>

        <h1>
          {mode === "login"
            ? "Welcome back"
            : "Create your account"}
        </h1>

        <p className="login-subtitle">
          {mode === "login"
            ? "Sign in to continue"
            : "Start your recruitment or job search journey"}
        </p>

        <div className="auth-tabs">
          <button
            type="button"
            className={mode === "login" ? "active" : ""}
            onClick={() => {
              setMode("login");
              setError("");
            }}
          >
            Sign In
          </button>

          <button
            type="button"
            className={mode === "register" ? "active" : ""}
            onClick={() => {
              setMode("register");
              setError("");
            }}
          >
            Create Account
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          {mode === "register" && (
            <>
              <label>Account type</label>

              <select
                value={accountType}
                onChange={(event) =>
                  setAccountType(event.target.value)
                }
              >
                <option value="RECRUITER">
                  Recruiter / Hiring Team
                </option>
                <option value="CANDIDATE">
                  Candidate / Job Seeker
                </option>
              </select>

              <div className="form-grid auth-name-grid">
                <div className="form-group">
                  <label>First name</label>
                  <input
                    value={firstName}
                    onChange={(event) =>
                      setFirstName(event.target.value)
                    }
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Last name</label>
                  <input
                    value={lastName}
                    onChange={(event) =>
                      setLastName(event.target.value)
                    }
                    required
                  />
                </div>
              </div>
            </>
          )}

          <label>Email</label>

          <input
            type="email"
            value={email}
            onChange={(event) =>
              setEmail(event.target.value)
            }
            placeholder="you@example.com"
            required
          />

          <label>Password</label>

          <input
            type="password"
            value={password}
            onChange={(event) =>
              setPassword(event.target.value)
            }
            placeholder="At least 8 characters"
            minLength={8}
            required
          />

          {error && (
            <div className="login-error">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
          >
            {loading
              ? "Please wait..."
              : mode === "login"
                ? "Sign In"
                : "Create Account"}
          </button>
        </form>
      </div>
    </div>
  );
}

// =====================================================
// CANDIDATE DASHBOARD
// =====================================================

function CandidateDashboard({ onLogout }) {
  const [profile, setProfile] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [applications, setApplications] = useState([]);
  const [resumes, setResumes] = useState([]);
  const [search, setSearch] = useState("");
  const [selectedJob, setSelectedJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [coverLetter, setCoverLetter] = useState("");
  const [profileForm, setProfileForm] = useState({
    headline: "",
    phone: "",
    location: "",
    total_experience_years: 0,
    current_company: "",
    current_title: "",
    bio: "",
  });

  function logout() {
    onLogout();
  }

  async function loadAll() {
    setLoading(true);
    setError("");

    try {
      const results = await Promise.allSettled([
        api.get("/candidates/profile"),
        api.get("/jobs/public"),
        api.get("/applications/mine"),
        api.get("/candidates/resumes"),
      ]);

      const [profileResult, jobsResult, applicationsResult, resumesResult] = results;

      if (profileResult.status === "fulfilled") {
        setProfile(profileResult.value.data);
        setProfileForm({
          headline: profileResult.value.data.headline || "",
          phone: profileResult.value.data.phone || "",
          location: profileResult.value.data.location || "",
          total_experience_years: profileResult.value.data.total_experience_years ?? 0,
          current_company: profileResult.value.data.current_company || "",
          current_title: profileResult.value.data.current_title || "",
          bio: profileResult.value.data.bio || "",
        });
      } else if (profileResult.reason?.response?.status === 404) {
        setProfile(null);
      }

      if (jobsResult.status === "fulfilled") {
        setJobs(Array.isArray(jobsResult.value.data) ? jobsResult.value.data : []);
      }

      if (applicationsResult.status === "fulfilled") {
        setApplications(
          Array.isArray(applicationsResult.value.data)
            ? applicationsResult.value.data
            : []
        );
      }

      if (resumesResult.status === "fulfilled") {
        setResumes(
          Array.isArray(resumesResult.value.data)
            ? resumesResult.value.data
            : []
        );
      }

      const firstError = results.find((item) => item.status === "rejected");
      if (firstError && firstError.reason?.response?.status === 401) {
        logout();
        return;
      }

      if (firstError && !profileResult.value) {
        console.error("Candidate dashboard load error:", firstError.reason);
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAll();
  }, []);

  async function saveProfile(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");

    try {
      const payload = {
        ...profileForm,
        total_experience_years:
          Number(profileForm.total_experience_years) || 0,
      };

      const response = profile
        ? await api.patch("/candidates/profile", payload)
        : await api.post("/candidates/profile", payload);

      setProfile(response.data);
      setMessage("Profile saved successfully.");
    } catch (error) {
      console.error("Profile save error:", error.response?.data || error);
      if (error.response?.status === 401) {
        logout();
        return;
      }
      setError(
        error.response?.data?.detail ||
          "Could not save candidate profile."
      );
    } finally {
      setBusy(false);
    }
  }

  async function uploadResume(event) {
    const file = event.target.files?.[0];
    event.target.value = "";

    if (!file) return;

    const allowed = [
      "application/pdf",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ];

    if (!allowed.includes(file.type)) {
      setError("Only PDF and DOCX resumes are supported.");
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setError("Resume file must be 5 MB or smaller.");
      return;
    }

    setBusy(true);
    setError("");
    setMessage("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      await api.post("/candidates/resumes", formData);
      setMessage("Resume uploaded successfully. Run AI Analysis to analyze it.");
      await loadAll();
    } catch (error) {
      console.error("Resume upload error:", error.response?.data || error);
      if (error.response?.status === 401) {
        logout();
        return;
      }
      setError(
        error.response?.data?.detail ||
          "Could not upload resume."
      );
    } finally {
      setBusy(false);
    }
  }

  async function analyzeResume(resumeId) {
    setBusy(true);
    setError("");
    setMessage("");

    try {
      const response = await api.post(
        `/candidates/resumes/${resumeId}/analyze`
      );

      setMessage(
        response.data?.message ||
          "AI resume analysis completed successfully."
      );

      await loadAll();
    } catch (error) {
      console.error(
        "AI resume analysis error:",
        error.response?.data || error
      );

      if (error.response?.status === 401) {
        logout();
        return;
      }

      setError(
        error.response?.data?.detail ||
          "AI resume analysis failed."
      );
    } finally {
      setBusy(false);
    }
  }

  async function deleteResume(resumeId, filename) {
    const confirmed = window.confirm(
      `Delete "${filename}"? This will also delete its AI analysis.`
    );

    if (!confirmed) return;

    setBusy(true);
    setError("");
    setMessage("");

    try {
      await api.delete(`/candidates/resumes/${resumeId}`);
      setMessage("Resume deleted successfully.");
      await loadAll();
    } catch (error) {
      console.error("Resume delete error:", error.response?.data || error);
      if (error.response?.status === 401) {
        logout();
        return;
      }
      setError(
        error.response?.data?.detail ||
          "Could not delete resume."
      );
    } finally {
      setBusy(false);
    }
  }

  async function applyToJob(job) {
    if (!job?.id) return;

    setBusy(true);
    setError("");
    setMessage("");

    try {
      await api.post(
        `/applications/jobs/${job.id}/apply`,
        null,
        {
          params: {
            cover_letter: coverLetter.trim() || undefined,
          },
        }
      );

      setCoverLetter("");
      setSelectedJob(null);
      setMessage(`Application submitted for ${job.title}.`);
      await loadAll();
    } catch (error) {
      console.error("Application error:", error.response?.data || error);
      if (error.response?.status === 401) {
        logout();
        return;
      }
      setError(
        error.response?.data?.detail ||
          "Could not submit application."
      );
    } finally {
      setBusy(false);
    }
  }

  const appliedJobIds = useMemo(
    () => new Set(applications.map((item) => item.job_id)),
    [applications]
  );

  const filteredJobs = useMemo(() => {
    const query = search.trim().toLowerCase();

    if (!query) return jobs;

    return jobs.filter((job) =>
      [
        job.title,
        job.department,
        job.location,
        job.description,
        job.employment_type,
      ]
        .filter(Boolean)
        .some((value) =>
          String(value).toLowerCase().includes(query)
        )
    );
  }, [jobs, search]);

  if (loading) {
    return (
      <div className="page">
        <div className="loading-card">Loading candidate dashboard...</div>
      </div>
    );
  }

  return (
    <div className="page">
      <header className="header">
        <div>
          <h1>AI Recruitment Platform</h1>
          <p>Candidate Workspace</p>
        </div>
        <button className="logout-button" onClick={logout}>
          Logout
        </button>
      </header>

      <main className="dashboard">
        {error && <div className="dashboard-error">{error}</div>}
        {message && <div className="dashboard-success">{message}</div>}

        <section className="details-card">
          <div className="section-heading">
            <div>
              <h2 className="section-title">My Profile</h2>
              <p className="section-description">
                Keep your candidate information current.
              </p>
            </div>
          </div>

          <form onSubmit={saveProfile}>
            <div className="form-grid">
              <div className="form-group">
                <label>Headline</label>
                <input
                  value={profileForm.headline}
                  onChange={(e) =>
                    setProfileForm((v) => ({
                      ...v,
                      headline: e.target.value,
                    }))
                  }
                  placeholder="Python Backend Developer"
                />
              </div>

              <div className="form-group">
                <label>Current title</label>
                <input
                  value={profileForm.current_title}
                  onChange={(e) =>
                    setProfileForm((v) => ({
                      ...v,
                      current_title: e.target.value,
                    }))
                  }
                />
              </div>

              <div className="form-group">
                <label>Current company</label>
                <input
                  value={profileForm.current_company}
                  onChange={(e) =>
                    setProfileForm((v) => ({
                      ...v,
                      current_company: e.target.value,
                    }))
                  }
                />
              </div>

              <div className="form-group">
                <label>Phone</label>
                <input
                  value={profileForm.phone}
                  onChange={(e) =>
                    setProfileForm((v) => ({
                      ...v,
                      phone: e.target.value,
                    }))
                  }
                />
              </div>

              <div className="form-group">
                <label>Location</label>
                <input
                  value={profileForm.location}
                  onChange={(e) =>
                    setProfileForm((v) => ({
                      ...v,
                      location: e.target.value,
                    }))
                  }
                />
              </div>

              <div className="form-group">
                <label>Experience (years)</label>
                <input
                  type="number"
                  min="0"
                  max="60"
                  step="0.1"
                  value={profileForm.total_experience_years}
                  onChange={(e) =>
                    setProfileForm((v) => ({
                      ...v,
                      total_experience_years: e.target.value,
                    }))
                  }
                />
              </div>
            </div>

            <div className="form-group">
              <label>Bio</label>
              <textarea
                rows="4"
                value={profileForm.bio}
                onChange={(e) =>
                  setProfileForm((v) => ({
                    ...v,
                    bio: e.target.value,
                  }))
                }
              />
            </div>

            <button className="primary-button" disabled={busy}>
              {busy ? "Saving..." : "Save Profile"}
            </button>
          </form>
        </section>

        <section className="details-card">
          <div className="section-heading">
            <div>
              <h2 className="section-title">My Resumes</h2>
              <p className="section-description">
                Upload up to 5 resumes and run AI analysis on each one.
              </p>
            </div>

            <label className="primary-button">
              Upload Resume
              <input
                type="file"
                accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                onChange={uploadResume}
                disabled={busy || resumes.length >= 5}
                hidden
              />
            </label>
          </div>

          {resumes.length === 0 ? (
            <div className="empty-card">
              <h3>No resumes uploaded</h3>
              <p>Upload your PDF or DOCX resume to start AI analysis.</p>
            </div>
          ) : (
            <div className="jobs-grid">
              {resumes.map((resume) => (
                <div className="job-card" key={resume.id}>
                  <div className="job-card-header">
                    <div>
                      <h3>{resume.original_filename}</h3>
                      <p>
                        {Math.round((resume.file_size || 0) / 1024)} KB
                      </p>
                    </div>
                  </div>

                  <div className="job-description">
                    {resume.analysis ? (
                      <>
                        <strong>AI Summary</strong>
                        <p>
                          {resume.analysis.summary ||
                            "Analysis completed."}
                        </p>

                        <strong>Skills</strong>
                        <div className="skill-list">
                          {resume.analysis.skills?.length ? (
                            resume.analysis.skills.map((skill) => (
                              <span
                                className="skill matching"
                                key={skill}
                              >
                                {skill}
                              </span>
                            ))
                          ) : (
                            <span className="muted">
                              No skills extracted.
                            </span>
                          )}
                        </div>
                      </>
                    ) : (
                      <p className="muted">
                        AI analysis has not been run yet.
                      </p>
                    )}
                  </div>

                  <div className="job-footer-actions">
                    <button
                      className="primary-button"
                      onClick={() => analyzeResume(resume.id)}
                      disabled={busy}
                    >
                      {resume.analysis
                        ? "Re-run AI Analysis"
                        : "Run AI Analysis"}
                    </button>

                    <button
                      className="danger-button"
                      onClick={() =>
                        deleteResume(
                          resume.id,
                          resume.original_filename
                        )
                      }
                      disabled={busy}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="jobs-section">
          <div className="section-heading">
            <div>
              <h2 className="section-title">Find Jobs</h2>
              <p className="section-description">
                Browse published opportunities and apply directly.
              </p>
            </div>

            <input
              className="candidate-search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search jobs..."
            />
          </div>

          {filteredJobs.length === 0 ? (
            <div className="empty-card">
              <h3>No published jobs found</h3>
              <p>Try another search or check again later.</p>
            </div>
          ) : (
            <div className="jobs-grid">
              {filteredJobs.map((job) => {
                const applied = appliedJobIds.has(job.id);

                return (
                  <div className="job-card" key={job.id}>
                    <div className="job-card-header">
                      <div>
                        <h3>{job.title}</h3>
                        <p>
                          {job.department || "General"} ·{" "}
                          {job.location || "Location not specified"}
                        </p>
                      </div>

                      {job.is_remote && (
                        <span className="status-badge">Remote</span>
                      )}
                    </div>

                    <div className="job-description">
                      <p>{job.description}</p>
                    </div>

                    <div className="job-footer">
                      <span>{job.employment_type}</span>
                      {job.experience_min !== null &&
                        job.experience_min !== undefined && (
                          <span>
                            {job.experience_min}-
                            {job.experience_max ?? "+"} years
                          </span>
                        )}
                    </div>

                    <div className="job-footer-actions">
                      <button
                        className="primary-button"
                        disabled={applied || busy}
                        onClick={() => {
                          setSelectedJob(job);
                          setCoverLetter("");
                        }}
                      >
                        {applied ? "Applied" : "Apply Now"}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        <section className="details-card">
          <h2 className="section-title">My Applications</h2>

          {applications.length === 0 ? (
            <div className="empty-card">
              <h3>No applications yet</h3>
              <p>Applications you submit will appear here.</p>
            </div>
          ) : (
            <div className="jobs-grid">
              {applications.map((application) => (
                <div className="job-card" key={application.id}>
                  <h3>{application.job_title}</h3>
                  <p>Status: {application.status}</p>
                  <p className="muted">
                    Applied:{" "}
                    {application.applied_at
                      ? new Date(
                          application.applied_at
                        ).toLocaleString()
                      : "-"}
                  </p>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>

      {selectedJob && (
        <div className="modal-overlay">
          <div className="modal-card">
            <div className="section-heading">
              <div>
                <h2>Apply for {selectedJob.title}</h2>
                <p className="section-description">
                  Add an optional cover letter.
                </p>
              </div>

              <button
                className="close-button"
                onClick={() => setSelectedJob(null)}
              >
                Close
              </button>
            </div>

            <textarea
              rows="8"
              value={coverLetter}
              onChange={(e) => setCoverLetter(e.target.value)}
              placeholder="Write a short cover letter..."
            />

            <div className="job-footer-actions">
              <button
                className="primary-button"
                disabled={busy}
                onClick={() => applyToJob(selectedJob)}
              >
                {busy ? "Submitting..." : "Submit Application"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// =====================================================
// DASHBOARD
// =====================================================

function Dashboard({ onLogout }) {
  const [dashboard, setDashboard] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [candidates, setCandidates] = useState([]);

  // Job skills
  const [jobSkills, setJobSkills] = useState([]);
  const [loadingJobSkills, setLoadingJobSkills] = useState(false);
  const [showJobSkills, setShowJobSkills] = useState(null);

  // Candidate filters
  const [candidateSearch, setCandidateSearch] =
    useState("");

  const [candidateStatusFilter, setCandidateStatusFilter] =
    useState("ALL");

  const [candidateSort, setCandidateSort] =
    useState("MATCH");

  const [candidateDetails, setCandidateDetails] =
    useState(null);

  const [loadingJobs, setLoadingJobs] =
    useState(false);

  const [loadingCandidates, setLoadingCandidates] =
    useState(false);

  const [loadingDetails, setLoadingDetails] =
    useState(false);

  const [showCreateJob, setShowCreateJob] =
    useState(false);

  const [error, setError] = useState("");

  // ===================================================
  // LOGOUT
  // ===================================================

  function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("organization_id");
    onLogout();
  }

  // ===================================================
  // LOAD DASHBOARD
  // ===================================================

  async function loadDashboard() {
    try {
      const response = await api.get(
        "/dashboard/recruiter"
      );

      setDashboard(response.data);
    } catch (error) {
      console.error(
        "Dashboard error:",
        error.response?.data || error
      );

      if (error.response?.status === 401) {
        logout();
        return;
      }

      setError(
        "Could not load dashboard."
      );
    }
  }

  // ===================================================
  // LOAD JOBS
  // ===================================================

  async function loadJobs() {
    setLoadingJobs(true);

    try {
      const response = await api.get("/jobs");

      setJobs(
        Array.isArray(response.data)
          ? response.data
          : []
      );
    } catch (error) {
      console.error(
        "Jobs error:",
        error.response?.data || error
      );

      if (error.response?.status === 401) {
        logout();
        return;
      }

      setError(
        error.response?.data?.detail ||
          "Could not load jobs."
      );
    } finally {
      setLoadingJobs(false);
    }
  }


  async function deleteJob(job) {
  if (!job?.id) {
    setError("Job ID is missing.");
    return;
  }

  const confirmed = window.confirm(
    `Delete "${job.title}"?\n\nThis will remove the job from active listings. Existing applications will be preserved.`
  );

  if (!confirmed) {
    return;
  }

  setError("");

  try {
    await api.delete(`/jobs/${job.id}`);

    // Remove it immediately from the recruiter UI.
    setJobs((currentJobs) =>
      currentJobs.filter(
        (item) => item.id !== job.id
      )
    );

    // Close any open job-related panels.
    if (selectedJob?.id === job.id) {
      setSelectedJob(null);
      setCandidates([]);
      setCandidateDetails(null);
    }

    if (showJobSkills?.id === job.id) {
      setShowJobSkills(null);
      setJobSkills([]);
    }

    await loadDashboard();

  } catch (error) {
    console.error(
      "Delete job error:",
      error.response?.data || error
    );

    if (error.response?.status === 401) {
      logout();
      return;
    }

    setError(
      error.response?.data?.detail ||
        "Could not delete job."
    );
  }
}

  // ===================================================
  // JOB SKILLS
  // ===================================================

  async function loadJobSkills(jobId) {
    if (!jobId) return;

    setLoadingJobSkills(true);
    setError("");

    try {
      const response = await api.get(
        `/jobs/${jobId}/skills`
      );

      setJobSkills(
        Array.isArray(response.data)
          ? response.data
          : []
      );
    } catch (error) {
      console.error(
        "Job skills error:",
        error.response?.data || error
      );

      if (error.response?.status === 401) {
        logout();
        return;
      }

      setError(
        error.response?.data?.detail ||
          "Could not load job skills."
      );
    } finally {
      setLoadingJobSkills(false);
    }
  }

  async function addJobSkill(
    jobId,
    skillId,
    requiredYears
  ) {
    if (!jobId || !skillId) {
      setError("Skill ID is required.");
      return false;
    }

    try {
      setError("");

      await api.post(
        `/jobs/${jobId}/skills`,
        null,
        {
          params: {
            skill_id: skillId,
            required_years:
              Number(requiredYears) || 0,
          },
        }
      );

      await loadJobSkills(jobId);
      return true;
    } catch (error) {
      console.error(
        "Add job skill error:",
        error.response?.data || error
      );

      if (error.response?.status === 401) {
        logout();
        return false;
      }

      setError(
        error.response?.data?.detail ||
          "Could not add job skill."
      );
      return false;
    }
  }

  // ===================================================
  // LOAD MATCHES
  // ===================================================

  async function loadJobMatches(jobId) {
    try {
      const response = await api.get(
        `/jobs/${jobId}/matches`
      );

      return Array.isArray(response.data)
        ? response.data
        : [];
    } catch (error) {
      console.error(
        "Job matches error:",
        error.response?.data || error
      );

      if (error.response?.status === 401) {
        logout();
      }

      return [];
    }
  }

  // ===================================================
  // LOAD CANDIDATES + MATCHES
  // ===================================================

  async function loadCandidates(job) {
    if (!job?.id) {
      setError("Job ID is missing.");
      return;
    }

    setSelectedJob(job);
    setCandidates([]);
    setCandidateDetails(null);

    // Reset filters when opening another job
    setCandidateSearch("");
    setCandidateStatusFilter("ALL");
    setCandidateSort("MATCH");

    setError("");
    setLoadingCandidates(true);

    try {
      const candidatesResponse =
        await api.get(
          `/recruiter/jobs/${job.id}/candidates`
        );

      const recruiterCandidates =
        Array.isArray(candidatesResponse.data)
          ? candidatesResponse.data
          : [];

      const matches =
        await loadJobMatches(job.id);

      const matchMap = new Map();

      matches.forEach((match) => {
        matchMap.set(
          match.candidate_id,
          match
        );
      });

      const mergedCandidates =
        recruiterCandidates.map(
          (candidate) => {
            const match =
              matchMap.get(
                candidate.candidate_id
              );

            if (!match) {
              return candidate;
            }

            return {
              ...candidate,

              match_score:
                match.match_score ??
                candidate.match_score ??
                0,

              matching_skills:
                match.matching_skills ??
                candidate.matching_skills ??
                [],

              missing_skills:
                match.missing_skills ??
                candidate.missing_skills ??
                [],

              recommendation:
                match.recommendation ??
                candidate.recommendation ??
                null,
            };
          }
        );

      mergedCandidates.sort(
        (a, b) =>
          (b.match_score ?? 0) -
          (a.match_score ?? 0)
      );

      setCandidates(
        mergedCandidates
      );
    } catch (error) {
      console.error(
        "Candidates error:",
        error.response?.data || error
      );

      if (error.response?.status === 401) {
        logout();
        return;
      }

      setError(
        error.response?.data?.detail ||
          "Could not load candidates."
      );
    } finally {
      setLoadingCandidates(false);
    }
  }

  // ===================================================
  // FILTER + SORT CANDIDATES
  // ===================================================

  const filteredCandidates = useMemo(() => {
    let result = [...candidates];

    // SEARCH
    const search =
      candidateSearch
        .trim()
        .toLowerCase();

    if (search) {
      result = result.filter(
        (candidate) => {
          const candidateId =
            candidate.candidate_id
              ?.toLowerCase() || "";

          const applicationId =
            candidate.application_id
              ?.toLowerCase() || "";

          return (
            candidateId.includes(search) ||
            applicationId.includes(search)
          );
        }
      );
    }

    // STATUS FILTER
    if (
      candidateStatusFilter !== "ALL"
    ) {
      result = result.filter(
        (candidate) =>
          candidate.status ===
          candidateStatusFilter
      );
    }

    // SORT
    if (candidateSort === "MATCH") {
      result.sort(
        (a, b) =>
          (b.match_score ?? 0) -
          (a.match_score ?? 0)
      );
    }

    if (
      candidateSort === "LOWEST_MATCH"
    ) {
      result.sort(
        (a, b) =>
          (a.match_score ?? 0) -
          (b.match_score ?? 0)
      );
    }

    if (candidateSort === "NEWEST") {
      result.sort(
        (a, b) =>
          new Date(
            b.applied_at || 0
          ) -
          new Date(
            a.applied_at || 0
          )
      );
    }

    if (candidateSort === "OLDEST") {
      result.sort(
        (a, b) =>
          new Date(
            a.applied_at || 0
          ) -
          new Date(
            b.applied_at || 0
          )
      );
    }

    return result;
  }, [
    candidates,
    candidateSearch,
    candidateStatusFilter,
    candidateSort,
  ]);

  // ===================================================
  // LOAD CANDIDATE DETAILS
  // ===================================================

  async function loadCandidateDetails(
    applicationId
  ) {
    if (!applicationId) {
      setError(
        "Application ID is missing."
      );
      return;
    }

    setLoadingDetails(true);
    setCandidateDetails(null);
    setError("");

    try {
      const response = await api.get(
        `/applications/${applicationId}/candidate`
      );

      setCandidateDetails(
        response.data
      );
    } catch (error) {
      console.error(
        "Candidate details error:",
        error.response?.data || error
      );

      if (error.response?.status === 401) {
        logout();
        return;
      }

      setError(
        error.response?.data?.detail ||
          "Could not load candidate details."
      );
    } finally {
      setLoadingDetails(false);
    }
  }

  // ===================================================
  // UPDATE APPLICATION STATUS
  // ===================================================

  async function updateApplicationStatus(
    applicationId,
    newStatus
  ) {
    if (
      !applicationId ||
      !newStatus
    ) {
      return;
    }

    try {
      setError("");

      await api.patch(
        `/applications/${applicationId}/status`,
        null,
        {
          params: {
            new_status: newStatus,
          },
        }
      );

      setCandidates(
        (currentCandidates) =>
          currentCandidates.map(
            (candidate) =>
              candidate.application_id ===
              applicationId
                ? {
                    ...candidate,
                    status: newStatus,
                  }
                : candidate
          )
      );

      setCandidateDetails(
        (currentDetails) => {
          if (!currentDetails) {
            return currentDetails;
          }

          return {
            ...currentDetails,

            application:
              currentDetails.application
                ? {
                    ...currentDetails.application,
                    status: newStatus,
                  }
                : currentDetails.application,
          };
        }
      );

      await loadDashboard();
    } catch (error) {
      console.error(
        "Status update error:",
        error.response?.data || error
      );

      if (error.response?.status === 401) {
        logout();
        return;
      }

      setError(
        error.response?.data?.detail ||
          "Could not update application status."
      );
    }
  }

  // ===================================================
  // INITIAL LOAD
  // ===================================================

  useEffect(() => {
    loadDashboard();
    loadJobs();
  }, []);

  // ===================================================
  // ERROR
  // ===================================================

  if (error && !dashboard) {
    return (
      <div className="page">
        <div className="error">
          {error}
        </div>
      </div>
    );
  }

  // ===================================================
  // LOADING
  // ===================================================

  if (!dashboard) {
    return (
      <div className="page">
        <div className="loading">
          Loading dashboard...
        </div>
      </div>
    );
  }

  // ===================================================
  // DASHBOARD UI
  // ===================================================

  return (
    <div className="page">
      <header className="header">
        <div>
          <h1>
            AI Recruitment Platform
          </h1>

          <p>
            Recruiter Dashboard
          </p>
        </div>

        <button
          className="logout-button"
          onClick={logout}
        >
          Logout
        </button>
      </header>

      <main className="dashboard">

        {error && (
          <div className="dashboard-error">
            {error}
          </div>
        )}

        {/* OVERVIEW */}

        <section>
          <h2 className="section-title">
            Overview
          </h2>

          <div className="stats-grid">
            <StatCard
              title="Total Jobs"
              value={
                dashboard.total_jobs ?? 0
              }
            />

            <StatCard
              title="Published Jobs"
              value={
                dashboard.published_jobs ?? 0
              }
            />

            <StatCard
              title="Applications"
              value={
                dashboard.total_applications ?? 0
              }
            />

            <StatCard
              title="Shortlisted"
              value={
                dashboard.shortlisted ?? 0
              }
            />

            <StatCard
              title="Interviews"
              value={
                dashboard.interviews ?? 0
              }
            />

            <StatCard
              title="Hired"
              value={
                dashboard.hired ?? 0
              }
            />

            <StatCard
              title="Rejected"
              value={
                dashboard.rejected ?? 0
              }
            />

            <StatCard
              title="Average Match"
              value={`${dashboard.average_match_score ?? 0}%`}
            />
          </div>
        </section>

        {/* JOBS */}

        <section className="jobs-section">

          <div className="section-heading">
            <div>
              <h2 className="section-title">
                My Jobs
              </h2>

              <p className="section-description">
                Manage your job postings and
                candidates.
              </p>
            </div>

            <button
              className="primary-button"
              onClick={() =>
                setShowCreateJob(true)
              }
            >
              + Create Job
            </button>
          </div>

          {showCreateJob && (
            <CreateJobForm
              onClose={() =>
                setShowCreateJob(false)
              }
              onCreated={async () => {
                setShowCreateJob(false);
                await loadJobs();
                await loadDashboard();
              }}
              setError={setError}
            />
          )}

          <div className="job-count">
            {jobs.length} job
            {jobs.length !== 1
              ? "s"
              : ""}
          </div>

          {loadingJobs ? (
            <div className="loading-card">
              Loading jobs...
            </div>
          ) : jobs.length === 0 ? (
            <div className="empty-card">
              <h3>
                No jobs yet
              </h3>

              <p>
                Create your first job posting
                to start receiving candidates.
              </p>
            </div>
          ) : (
            <div className="jobs-grid">
              {jobs.map((job) => (
                <JobCard
                  key={job.id}
                  job={job}
                  onViewCandidates={
                    loadCandidates
                  }
                  onManageSkills={(job) => {
                    setShowJobSkills(job);
                    loadJobSkills(job.id);
                  }}
                    onDeleteJob={deleteJob}

                />
              ))}
            </div>
          )}
        </section>

        {/* JOB SKILLS */}

        {showJobSkills && (
          <section className="jobs-section">
            <JobSkillsManager
              job={showJobSkills}
              skills={jobSkills}
              loading={loadingJobSkills}
              onAddSkill={async (
                skillId,
                requiredYears
              ) =>
                addJobSkill(
                  showJobSkills.id,
                  skillId,
                  requiredYears
                )
              }
              onClose={() => {
                setShowJobSkills(null);
                setJobSkills([]);
                setError("");
              }}
            />
          </section>
        )}

        {/* CANDIDATES */}

        {selectedJob && (
          <section className="candidates-section">

            <div className="section-heading">
              <div>
                <h2 className="section-title">
                  Candidates
                </h2>

                <p className="section-description">
                  {selectedJob.title}
                </p>
              </div>

              <button
                className="close-button"
                onClick={() => {
                  setSelectedJob(null);
                  setCandidates([]);
                  setCandidateDetails(null);
                  setCandidateSearch("");
                  setCandidateStatusFilter(
                    "ALL"
                  );
                  setCandidateSort(
                    "MATCH"
                  );
                  setError("");
                }}
              >
                Close
              </button>
            </div>

            {/* CANDIDATE FILTERS */}

            {!loadingCandidates &&
              candidates.length > 0 && (
                <div className="candidate-filters">

                  <input
                    type="text"
                    className="candidate-search"
                    placeholder="Search candidate or application ID..."
                    value={candidateSearch}
                    onChange={(event) =>
                      setCandidateSearch(
                        event.target.value
                      )
                    }
                  />

                  <select
                    value={
                      candidateStatusFilter
                    }
                    onChange={(event) =>
                      setCandidateStatusFilter(
                        event.target.value
                      )
                    }
                  >
                    <option value="ALL">
                      All Statuses
                    </option>

                    <option value="APPLIED">
                      Applied
                    </option>

                    <option value="SCREENING">
                      Screening
                    </option>

                    <option value="SHORTLISTED">
                      Shortlisted
                    </option>

                    <option value="INTERVIEW">
                      Interview
                    </option>

                    <option value="OFFER">
                      Offer
                    </option>

                    <option value="HIRED">
                      Hired
                    </option>

                    <option value="REJECTED">
                      Rejected
                    </option>
                  </select>

                  <select
                    value={candidateSort}
                    onChange={(event) =>
                      setCandidateSort(
                        event.target.value
                      )
                    }
                  >
                    <option value="MATCH">
                      Highest Match
                    </option>

                    <option value="LOWEST_MATCH">
                      Lowest Match
                    </option>

                    <option value="NEWEST">
                      Newest Application
                    </option>

                    <option value="OLDEST">
                      Oldest Application
                    </option>
                  </select>
                </div>
              )}

            {loadingCandidates ? (
              <div className="loading-card">
                Loading candidates...
              </div>
            ) : candidates.length === 0 ? (
              <div className="empty-card">
                <h3>
                  No candidates found
                </h3>

                <p>
                  There are currently no
                  applications for this job.
                </p>
              </div>
            ) : filteredCandidates.length === 0 ? (
              <div className="empty-card">
                <h3>
                  No matching candidates
                </h3>

                <p>
                  Try changing your search
                  or filters.
                </p>
              </div>
            ) : (
              <div className="candidates-list">

                {filteredCandidates.map(
                  (candidate, index) => (
                    <CandidateCard
                      key={
                        candidate.application_id ||
                        candidate.candidate_id ||
                        index
                      }
                      candidate={candidate}
                      rank={index + 1}
                      onViewDetails={
                        loadCandidateDetails
                      }
                      onStatusChange={
                        updateApplicationStatus
                      }
                    />
                  )
                )}

              </div>
            )}

            {/* DETAILS */}

            {loadingDetails && (
              <div className="loading-card">
                Loading candidate details...
              </div>
            )}

            {candidateDetails &&
              !loadingDetails && (
                <CandidateDetails
                  details={candidateDetails}
                  onClose={() =>
                    setCandidateDetails(null)
                  }
                  onStatusChange={
                    updateApplicationStatus
                  }
                />
              )}

          </section>
        )}

      </main>
    </div>
  );
}

// =====================================================
// CREATE JOB
// =====================================================

function CreateJobForm({
  onClose,
  onCreated,
  setError,
}) {
  const [form, setForm] = useState({
    title: "",
    slug: "",
    description: "",
    department: "",
    location: "",
    is_remote: false,
    employment_type: "FULL_TIME",
    experience_min: "",
    experience_max: "",
    salary_min: "",
    salary_max: "",
    status: "DRAFT",
  });

  const [loading, setLoading] =
    useState(false);

  const [formError, setFormError] =
    useState("");

  function updateField(
    field,
    value
  ) {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  }

  function generateSlug(title) {
    return title
      .toLowerCase()
      .trim()
      .replace(
        /[^a-z0-9]+/g,
        "-"
      )
      .replace(
        /^-|-$/g,
        "");
  }

  async function handleSubmit(event) {
    event.preventDefault();

    setLoading(true);
    setFormError("");
    setError("");

    try {
      const organizationId =
        localStorage.getItem(
          "organization_id"
        );

      if (!organizationId) {
        setFormError(
          "Organization ID is missing. Please logout and login again."
        );
        return;
      }

      const generatedSlug =
        form.slug ||
        generateSlug(form.title);

      const payload = {
        organization_id:
          organizationId,

        title: form.title,

        slug: generatedSlug,

        description:
          form.description,

        department:
          form.department || null,

        location:
          form.location || null,

        is_remote:
          form.is_remote,

        employment_type:
          form.employment_type,

        experience_min:
          form.experience_min !== ""
            ? Number(
                form.experience_min
              )
            : null,

        experience_max:
          form.experience_max !== ""
            ? Number(
                form.experience_max
              )
            : null,

        salary_min:
          form.salary_min !== ""
            ? Number(
                form.salary_min
              )
            : null,

        salary_max:
          form.salary_max !== ""
            ? Number(
                form.salary_max
              )
            : null,

        status: form.status,
      };

      console.log(
        "Creating job:",
        payload
      );

      await api.post(
        "/jobs",
        payload
      );

      onCreated();
    } catch (error) {
      console.error(
        "Create job error:",
        error.response?.data || error
      );

      if (
        error.response?.status === 401
      ) {
        localStorage.removeItem(
          "access_token"
        );

        setFormError(
          "Session expired. Please login again."
        );

        window.location.reload();
        return;
      }

      const detail =
        error.response?.data?.detail;

      if (Array.isArray(detail)) {
        setFormError(
          detail
            .map(
              (item) =>
                item.msg
            )
            .join(", ")
        );
      } else {
        setFormError(
          detail ||
            "Could not create job."
        );
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="create-job-card">

      <div className="section-heading">

        <div>
          <h2 className="section-title">
            Create Job
          </h2>

          <p className="section-description">
            Create a new recruitment position.
          </p>
        </div>

        <button
          className="close-button"
          type="button"
          onClick={onClose}
        >
          Cancel
        </button>

      </div>

      {formError && (
        <div className="dashboard-error">
          {formError}
        </div>
      )}

      <form
        className="job-form"
        onSubmit={handleSubmit}
      >

        <div className="form-grid">

          <div className="form-group">
            <label>
              Job Title
            </label>

            <input
              value={form.title}
              onChange={(event) => {
                const title =
                  event.target.value;

                setForm((current) => ({
                  ...current,
                  title,
                  slug:
                    current.slug ||
                    generateSlug(title),
                }));
              }}
              placeholder="Python Backend Developer"
              required
            />
          </div>

          <div className="form-group">
            <label>
              Slug
            </label>

            <input
              value={form.slug}
              onChange={(event) =>
                updateField(
                  "slug",
                  event.target.value
                )
              }
              placeholder="python-backend-developer"
              required
            />
          </div>

          <div className="form-group">
            <label>
              Department
            </label>

            <input
              value={form.department}
              onChange={(event) =>
                updateField(
                  "department",
                  event.target.value
                )
              }
              placeholder="Engineering"
            />
          </div>

          <div className="form-group">
            <label>
              Location
            </label>

            <input
              value={form.location}
              onChange={(event) =>
                updateField(
                  "location",
                  event.target.value
                )
              }
              placeholder="Hyderabad"
            />
          </div>

          <div className="form-group">
            <label>
              Employment Type
            </label>

            <select
              value={
                form.employment_type
              }
              onChange={(event) =>
                updateField(
                  "employment_type",
                  event.target.value
                )
              }
            >
              <option value="FULL_TIME">
                Full Time
              </option>

              <option value="PART_TIME">
                Part Time
              </option>

              <option value="CONTRACT">
                Contract
              </option>

              <option value="INTERNSHIP">
                Internship
              </option>
            </select>
          </div>

          <div className="form-group">
            <label>
              Status
            </label>

            <select
              value={form.status}
              onChange={(event) =>
                updateField(
                  "status",
                  event.target.value
                )
              }
            >
              <option value="DRAFT">
                Draft
              </option>

              <option value="PUBLISHED">
                Published
              </option>
            </select>
          </div>

          <div className="form-group">
            <label>
              Minimum Experience
            </label>

            <input
              type="number"
              min="0"
              value={
                form.experience_min
              }
              onChange={(event) =>
                updateField(
                  "experience_min",
                  event.target.value
                )
              }
              placeholder="1"
            />
          </div>

          <div className="form-group">
            <label>
              Maximum Experience
            </label>

            <input
              type="number"
              min="0"
              value={
                form.experience_max
              }
              onChange={(event) =>
                updateField(
                  "experience_max",
                  event.target.value
                )
              }
              placeholder="5"
            />
          </div>

          <div className="form-group">
            <label>
              Minimum Salary
            </label>

            <input
              type="number"
              min="0"
              value={
                form.salary_min
              }
              onChange={(event) =>
                updateField(
                  "salary_min",
                  event.target.value
                )
              }
              placeholder="600000"
            />
          </div>

          <div className="form-group">
            <label>
              Maximum Salary
            </label>

            <input
              type="number"
              min="0"
              value={
                form.salary_max
              }
              onChange={(event) =>
                updateField(
                  "salary_max",
                  event.target.value
                )
              }
              placeholder="1000000"
            />
          </div>

        </div>

        <div className="form-group">
          <label>
            Description
          </label>

          <textarea
            value={
              form.description
            }
            onChange={(event) =>
              updateField(
                "description",
                event.target.value
              )
            }
            placeholder="Describe the role, responsibilities and requirements..."
            rows="6"
            required
          />
        </div>

        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={
              form.is_remote
            }
            onChange={(event) =>
              updateField(
                "is_remote",
                event.target.checked
              )
            }
          />

          Remote position
        </label>

        <div className="form-actions">

          <button
            type="button"
            className="close-button"
            onClick={onClose}
          >
            Cancel
          </button>

          <button
            type="submit"
            className="primary-button"
            disabled={loading}
          >
            {loading
              ? "Creating..."
              : "Create Job"}
          </button>

        </div>

      </form>
    </div>
  );
}

// =====================================================
// STAT CARD
// =====================================================

function StatCard({
  title,
  value,
}) {
  return (
    <div className="stat-card">
      <p>{title}</p>
      <h2>{value}</h2>
    </div>
  );
}

// =====================================================
// JOB CARD
// =====================================================

function JobCard({
  job,
  onViewCandidates,
  onManageSkills,
    onDeleteJob,

}) {
  return (
    <div className="job-card">

      <div className="job-card-top">

        <div>
          <h3>
            {job.title}
          </h3>

          <p className="job-slug">
            {job.slug}
          </p>
        </div>

        <span
          className={`status-badge status-${String(
            job.status || ""
          ).toLowerCase()}`}
        >
          {job.status}
        </span>

      </div>

      {job.description && (
        <p className="job-description">
          {job.description}
        </p>
      )}

      <div className="job-meta">

        {job.department && (
          <span>
            🏢 {job.department}
          </span>
        )}

        {job.location && (
          <span>
            📍 {job.location}
          </span>
        )}

        {job.is_remote && (
          <span>
            🌐 Remote
          </span>
        )}

        {job.employment_type && (
          <span>
            💼 {job.employment_type}
          </span>
        )}

        {job.salary_min !== null &&
          job.salary_min !==
            undefined && (
            <span>
              💰 ₹
              {Number(
                job.salary_min
              ).toLocaleString()}
            </span>
          )}

        {job.salary_max !== null &&
          job.salary_max !==
            undefined && (
            <span>
              - ₹
              {Number(
                job.salary_max
              ).toLocaleString()}
            </span>
          )}

      </div>

      <div className="job-footer">

        <div className="experience">
          {job.experience_min !== null &&
            job.experience_min !==
              undefined &&
            job.experience_max !== null &&
            job.experience_max !==
              undefined && (
              <span>
                Experience:{" "}
                {job.experience_min}-
                {job.experience_max} years
              </span>
            )}
        </div>

        <div className="job-footer-actions">
          <button
            className="close-button"
            onClick={() =>
              onManageSkills(job)
            }
          >
            Manage Skills
          </button>

          <button
            className="primary-button"
            onClick={() =>
              onViewCandidates(job)
            }
          >
            View Candidates
          </button>

          <button
  type="button"
  className="danger-button"
  onClick={() => onDeleteJob(job)}
>
  Delete
</button>
        </div>

      </div>
    </div>
  );
}

// =====================================================
// =====================================================
// JOB SKILLS MANAGER
// =====================================================
function JobSkillsManager({
  job,
  skills,
  loading,
  onAddSkill,
  onClose,
}) {
  const [skillId, setSkillId] = useState("");
  const [requiredYears, setRequiredYears] = useState("0");
  const [adding, setAdding] = useState(false);
  const [localError, setLocalError] = useState("");

  const [availableSkills, setAvailableSkills] = useState([]);
  const [loadingAvailableSkills, setLoadingAvailableSkills] =
    useState(true);

  // Load the master skill list from the backend.
  useEffect(() => {
    let mounted = true;

    async function loadAvailableSkills() {
      try {
        setLoadingAvailableSkills(true);

        const response = await api.get("/skills");

        if (mounted) {
          setAvailableSkills(
            Array.isArray(response.data)
              ? response.data
              : []
          );
        }
      } catch (error) {
        console.error(
          "Failed to load available skills:",
          error.response?.data || error
        );

        if (mounted) {
          setAvailableSkills([]);
          setLocalError(
            error.response?.data?.detail ||
              "Could not load available skills."
          );
        }
      } finally {
        if (mounted) {
          setLoadingAvailableSkills(false);
        }
      }
    }

    loadAvailableSkills();

    return () => {
      mounted = false;
    };
  }, []);

  // IDs of skills already attached to this job.
  const attachedSkillIds = new Set(
    (skills || []).map(
      (skill) => String(skill.skill_id || skill.id)
    )
  );

  // Only show skills that are not already attached.
  const selectableSkills = availableSkills.filter(
    (skill) =>
      !attachedSkillIds.has(String(skill.id))
  );

  async function handleAdd(event) {
    event.preventDefault();

    if (!skillId) {
      setLocalError("Please select a skill.");
      return;
    }

    setAdding(true);
    setLocalError("");

    try {
      const result = await onAddSkill(
        skillId,
        requiredYears
      );

      if (result === false) {
        return;
      }

      setSkillId("");
      setRequiredYears("0");
    } catch (error) {
      console.error(
        "Add skill error:",
        error.response?.data || error
      );

      setLocalError(
        error.response?.data?.detail ||
          "Could not add this skill."
      );
    } finally {
      setAdding(false);
    }
  }

  return (
    <div className="details-card job-skills-manager">

      <div className="section-heading">
        <div>
          <h2 className="section-title">
            Required Skills
          </h2>

          <p className="section-description">
            Add the skills required for this job.
          </p>
        </div>

        <button
          type="button"
          className="close-button"
          onClick={onClose}
        >
          Close
        </button>
      </div>

      {loading ? (
        <div className="loading-card">
          Loading required skills...
        </div>
      ) : skills.length === 0 ? (
        <div className="empty-card">
          <h3>No required skills added yet.</h3>

          <p>
            Add the skills required for this job.
          </p>
        </div>
      ) : (
        <div className="job-skills-list">
          {skills.map((skill) => (
            <div
              className="job-skill-row"
              key={skill.id}
            >
              <div>
                <strong>
                  {skill.skill_name ||
                    skill.name ||
                    "Skill"}
                </strong>

                {skill.category && (
                  <span className="muted">
                    {skill.category}
                  </span>
                )}
              </div>

              <span className="job-skill-years">
                {skill.required_years ?? 0} years
              </span>
            </div>
          ))}
        </div>
      )}

      <form
        className="job-skill-form"
        onSubmit={handleAdd}
      >
        <h3>Add Required Skill</h3>

        <p className="section-description">
          Select a skill from the platform skill library.
        </p>

        {localError && (
          <div className="dashboard-error">
            {localError}
          </div>
        )}

        <div className="form-grid">

          <div className="form-group">
            <label htmlFor="required-skill">
              Skill
            </label>

            <select
              id="required-skill"
              value={skillId}
              onChange={(event) =>
                setSkillId(event.target.value)
              }
              disabled={
                adding ||
                loadingAvailableSkills
              }
              required
            >
              <option value="">
                {loadingAvailableSkills
                  ? "Loading skills..."
                  : "Select a skill"}
              </option>

              {selectableSkills.map(
                (skill) => (
                  <option
                    key={skill.id}
                    value={skill.id}
                  >
                    {skill.name}
                    {skill.category
                      ? ` — ${skill.category}`
                      : ""}
                  </option>
                )
              )}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="required-years">
              Required Years
            </label>

            <input
              id="required-years"
              type="number"
              min="0"
              max="50"
              step="0.5"
              value={requiredYears}
              onChange={(event) =>
                setRequiredYears(
                  event.target.value
                )
              }
              disabled={adding}
            />
          </div>

        </div>

        <div className="form-actions">
          <button
            type="submit"
            className="primary-button"
            disabled={
              adding ||
              loadingAvailableSkills ||
              !skillId
            }
          >
            {adding
              ? "Adding..."
              : "Add Skill"}
          </button>
        </div>

      </form>
    </div>
  );
}

// CANDIDATE CARD
// =====================================================

function CandidateCard({
  candidate,
  rank,
  onViewDetails,
  onStatusChange,
}) {
  const score =
    candidate.match_score ?? 0;

  const status =
    candidate.status ||
    "APPLIED";

  const statusSteps = {
    APPLIED: [
      "SCREENING",
      "REJECTED",
    ],

    SCREENING: [
      "SHORTLISTED",
      "REJECTED",
    ],

    SHORTLISTED: [
      "INTERVIEW",
      "REJECTED",
    ],

    INTERVIEW: [
      "OFFER",
      "REJECTED",
    ],

    OFFER: [
      "HIRED",
      "REJECTED",
    ],

    HIRED: [],

    REJECTED: [],
  };

  const nextActions =
    statusSteps[status] || [];

  return (
    <div className="candidate-card">

      <div className="candidate-header">

        <div className="candidate-rank">
          #{rank}
        </div>

        <div className="candidate-main">

          <h3>
            Candidate
          </h3>

          <p>
            ID:{" "}
            {candidate.candidate_id}
          </p>

        </div>

        <div className="match-score">

          <span>
            Match
          </span>

          <strong>
            {score}%
          </strong>

        </div>

      </div>

      <div className="candidate-content">

        <div className="candidate-column">

          <h4>
            Matching Skills
          </h4>

          <div className="skill-list">

            {candidate.matching_skills?.length ? (
              candidate.matching_skills.map(
                (skill) => (
                  <span
                    className="skill matching"
                    key={skill}
                  >
                    ✓ {skill}
                  </span>
                )
              )
            ) : (
              <span className="muted">
                None
              </span>
            )}

          </div>
        </div>

        <div className="candidate-column">

          <h4>
            Missing Skills
          </h4>

          <div className="skill-list">

            {candidate.missing_skills?.length ? (
              candidate.missing_skills.map(
                (skill) => (
                  <span
                    className="skill missing"
                    key={skill}
                  >
                    ✕ {skill}
                  </span>
                )
              )
            ) : (
              <span className="muted">
                None
              </span>
            )}

          </div>
        </div>

        <div className="candidate-column">

          <h4>
            Application Status
          </h4>

          <span
            className={`application-status status-${String(
              status
            ).toLowerCase()}`}
          >
            {status}
          </span>

          {candidate.recommendation && (
            <p className="recommendation">
              {candidate.recommendation}
            </p>
          )}

        </div>

      </div>

      <div className="candidate-actions">

        <button
          className="close-button"
          onClick={() =>
            onViewDetails(
              candidate.application_id
            )
          }
        >
          View Candidate
        </button>

        <div className="candidate-action-buttons">

          {nextActions.includes(
            "SCREENING"
          ) && (
            <button
              className="primary-button"
              onClick={() =>
                onStatusChange(
                  candidate.application_id,
                  "SCREENING"
                )
              }
            >
              Start Screening
            </button>
          )}

          {nextActions.includes(
            "SHORTLISTED"
          ) && (
            <button
              className="primary-button"
              onClick={() =>
                onStatusChange(
                  candidate.application_id,
                  "SHORTLISTED"
                )
              }
            >
              Shortlist
            </button>
          )}

          {nextActions.includes(
            "INTERVIEW"
          ) && (
            <button
              className="primary-button"
              onClick={() =>
                onStatusChange(
                  candidate.application_id,
                  "INTERVIEW"
                )
              }
            >
              Interview
            </button>
          )}

          {nextActions.includes(
            "OFFER"
          ) && (
            <button
              className="primary-button"
              onClick={() =>
                onStatusChange(
                  candidate.application_id,
                  "OFFER"
                )
              }
            >
              Make Offer
            </button>
          )}

          {nextActions.includes(
            "HIRED"
          ) && (
            <button
              className="primary-button"
              onClick={() =>
                onStatusChange(
                  candidate.application_id,
                  "HIRED"
                )
              }
            >
              Hire Candidate
            </button>
          )}

          {nextActions.includes(
            "REJECTED"
          ) && (
            <button
              className="danger-button"
              onClick={() =>
                onStatusChange(
                  candidate.application_id,
                  "REJECTED"
                )
              }
            >
              Reject
            </button>
          )}

        </div>
      </div>

    </div>
  );
}

// =====================================================
// CANDIDATE DETAILS
// =====================================================

function CandidateDetails({
  details,
  onClose,
  onStatusChange,
}) {
  const candidate =
    details?.candidate;

  const resume =
    details?.resume;

  const analysis =
    details?.analysis;

  const application =
    details?.application;

  const match =
    details?.match;

  return (
    <section className="candidate-details">

      <div className="section-heading">

        <div>
          <h2 className="section-title">
            Candidate Details
          </h2>

          <p className="section-description">
            Complete candidate profile and AI analysis
          </p>
        </div>

        <button
          className="close-button"
          onClick={onClose}
        >
          Close
        </button>

      </div>

      {/* PROFILE */}

      <div className="details-card">

        <h3>
          Candidate Profile
        </h3>

        <div className="details-grid">

          <div>
            <span className="detail-label">
              Candidate ID
            </span>

            <strong>
              {candidate?.id || "-"}
            </strong>
          </div>

          <div>
            <span className="detail-label">
              Name
            </span>

            <strong>
              {[
                candidate?.first_name,
                candidate?.last_name,
              ]
                .filter(Boolean)
                .join(" ") || "-"}
            </strong>
          </div>

          <div>
            <span className="detail-label">
              Email
            </span>

            <strong>
              {candidate?.email || "-"}
            </strong>
          </div>

          <div>
            <span className="detail-label">
              Phone
            </span>

            <strong>
              {candidate?.phone || "-"}
            </strong>
          </div>

          <div>
            <span className="detail-label">
              Location
            </span>

            <strong>
              {candidate?.location || "-"}
            </strong>
          </div>

          <div>
            <span className="detail-label">
              Headline
            </span>

            <strong>
              {candidate?.headline || "-"}
            </strong>
          </div>

          <div>
            <span className="detail-label">
              Current title
            </span>

            <strong>
              {candidate?.current_title || "-"}
            </strong>
          </div>

          <div>
            <span className="detail-label">
              Current company
            </span>

            <strong>
              {candidate?.current_company || "-"}
            </strong>
          </div>

          <div>
            <span className="detail-label">
              Experience
            </span>

            <strong>
              {candidate?.total_experience_years ?? 0} years
            </strong>
          </div>

          <div>
            <span className="detail-label">
              User ID
            </span>

            <strong>
              {candidate?.user_id || "-"}
            </strong>
          </div>

        </div>
      </div>

      {/* APPLICATION */}

      {application && (
        <div className="details-card">

          <h3>
            Application
          </h3>

          <div className="details-grid">

            <div>

              <span className="detail-label">
                Status
              </span>

              <select
                className="application-status-select"
                value={
                  application.status ||
                  "APPLIED"
                }
                onChange={(event) =>
                  onStatusChange(
                    application.id,
                    event.target.value
                  )
                }
              >
                <option value="APPLIED">
                  APPLIED
                </option>

                <option value="SCREENING">
                  SCREENING
                </option>

                <option value="SHORTLISTED">
                  SHORTLISTED
                </option>

                <option value="INTERVIEW">
                  INTERVIEW
                </option>

                <option value="OFFER">
                  OFFER
                </option>

                <option value="HIRED">
                  HIRED
                </option>

                <option value="REJECTED">
                  REJECTED
                </option>
              </select>

            </div>

            <div>

              <span className="detail-label">
                Applied At
              </span>

              <strong>
                {application.applied_at
                  ? new Date(
                      application.applied_at
                    ).toLocaleDateString()
                  : "-"}
              </strong>

            </div>

          </div>

          {application.cover_letter && (
            <div className="cover-letter">

              <span className="detail-label">
                Cover Letter
              </span>

              <p>
                {application.cover_letter}
              </p>

            </div>
          )}

        </div>
      )}

      {/* RESUME */}

      {resume && (
        <div className="details-card">

          <h3>
            Resume
          </h3>

          <div className="details-grid">

            <div>
              <span className="detail-label">
                File
              </span>

              <strong>
                {resume.original_filename}
              </strong>
            </div>

            <div>
              <span className="detail-label">
                Type
              </span>

              <strong>
                {resume.file_type}
              </strong>
            </div>

            <div>
              <span className="detail-label">
                Size
              </span>

              <strong>
                {resume.file_size
                  ? `${Math.round(
                      resume.file_size /
                        1024
                    )} KB`
                  : "-"}
              </strong>
            </div>

          </div>
        </div>
      )}

      {/* AI ANALYSIS */}

      {analysis && (
        <div className="details-card">

          <div className="ai-heading">

            <div>
              <h3>
                AI Resume Analysis
              </h3>

              <p>
                Automatically generated resume insights
              </p>
            </div>

          </div>

          {analysis.summary && (
            <div className="analysis-summary">

              <span className="detail-label">
                Summary
              </span>

              <p>
                {analysis.summary}
              </p>

            </div>
          )}

          <div className="analysis-section">

            <h4>
              Skills
            </h4>

            <div className="skill-list">

              {analysis.skills?.length ? (
                analysis.skills.map(
                  (skill) => (
                    <span
                      className="skill matching"
                      key={skill}
                    >
                      {skill}
                    </span>
                  )
                )
              ) : (
                <span className="muted">
                  No skills available
                </span>
              )}

            </div>
          </div>

          <div className="analysis-section">

            <h4>
              Experience
            </h4>

            <p>
              {analysis.experience_years ??
                0}{" "}
              years
            </p>

          </div>

          <div className="analysis-section">

            <h4>
              Education
            </h4>

            {analysis.education?.length ? (
              <ul>
                {analysis.education.map(
                  (item) => (
                    <li key={item}>
                      {item}
                    </li>
                  )
                )}
              </ul>
            ) : (
              <p className="muted">
                No education information available.
              </p>
            )}

          </div>

          <div className="analysis-section">

            <h4>
              Recommended Roles
            </h4>

            <div className="skill-list">

              {analysis.recommended_roles?.length ? (
                analysis.recommended_roles.map(
                  (role) => (
                    <span
                      className="skill"
                      key={role}
                    >
                      {role}
                    </span>
                  )
                )
              ) : (
                <span className="muted">
                  None
                </span>
              )}

            </div>
          </div>

          <div className="analysis-columns">

            <div>
              <h4>
                Strengths
              </h4>

              {analysis.strengths?.length ? (
                <ul>
                  {analysis.strengths.map(
                    (strength) => (
                      <li key={strength}>
                        {strength}
                      </li>
                    )
                  )}
                </ul>
              ) : (
                <p className="muted">
                  None
                </p>
              )}
            </div>

            <div>
              <h4>
                Missing Skills
              </h4>

              {analysis.missing_skills?.length ? (
                <ul>
                  {analysis.missing_skills.map(
                    (skill) => (
                      <li key={skill}>
                        {skill}
                      </li>
                    )
                  )}
                </ul>
              ) : (
                <p className="muted">
                  None
                </p>
              )}
            </div>

          </div>

        </div>
      )}

      {/* JOB MATCH */}

      {match && (
        <div className="details-card">

          <div className="match-details-header">

            <div>
              <h3>
                Job Match
              </h3>

              <p>
                Candidate compatibility with this job
              </p>
            </div>

            <div className="large-match-score">
              {match.score ??
                match.match_score ??
                0}
              %
            </div>

          </div>

          <div className="analysis-columns">

            <div>

              <h4>
                Matching Skills
              </h4>

              <div className="skill-list">

                {match.matching_skills?.length ? (
                  match.matching_skills.map(
                    (skill) => (
                      <span
                        className="skill matching"
                        key={skill}
                      >
                        ✓ {skill}
                      </span>
                    )
                  )
                ) : (
                  <span className="muted">
                    None
                  </span>
                )}

              </div>

            </div>

            <div>

              <h4>
                Missing Skills
              </h4>

              <div className="skill-list">

                {match.missing_skills?.length ? (
                  match.missing_skills.map(
                    (skill) => (
                      <span
                        className="skill missing"
                        key={skill}
                      >
                        ✕ {skill}
                      </span>
                    )
                  )
                ) : (
                  <span className="muted">
                    None
                  </span>
                )}

              </div>

            </div>

          </div>

          {match.recommendation && (
            <p className="recommendation">
              {match.recommendation}
            </p>
          )}

        </div>
      )}

    </section>
  );
}

export default App;

"use client";

import { useState, useEffect, useRef, ChangeEvent, FormEvent } from "react";
import { useRouter } from "next/navigation";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000";

interface Job {
  job_id: string;
  status: string;
  file_name: string;
  anomaly_flags?: string[];
  mismatch_details?: Record<string, string>;
  extracted_fields?: any;
  error?: string;
}

export default function Dashboard() {
  const [file, setFile] = useState<File | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string>("");
  const router = useRouter();
  const pollIntervals = useRef<Record<string, NodeJS.Timeout>>({});

  useEffect(() => {
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    if (!token) {
      router.push("/login");
    }

    // Cleanup intervals on unmount
    return () => {
      Object.values(pollIntervals.current).forEach(clearInterval);
      pollIntervals.current = {};
    };
  }, [router]);

  const startPolling = (job_id: string) => {
    const token = localStorage.getItem("token");

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_URL}/upload/job/${job_id}`, {
          headers: { "Authorization": `Bearer ${token}` }
        });

        if (res.ok) {
          const data = await res.json();
          setJobs((prev) =>
            prev.map((j) => (j.job_id === job_id ? { ...j, ...data } : j))
          );

          if (data.status === "completed" || data.status === "failed") {
            clearInterval(interval);
            delete pollIntervals.current[job_id];
          }
        }
      } catch (err) {
        console.error("Polling error:", err);
      }
    }, 3000);

    pollIntervals.current[job_id] = interval;
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setUploadError("");
    }
  };

  const handleUpload = async (e: FormEvent) => {
    e.preventDefault();
    // Cache the form element synchronously before any 'await' clears the event object
    const formElement = e.currentTarget as HTMLFormElement;
    
    if (!file) {
      setUploadError("Please select a CSV or PDF file first.");
      return;
    }

    setUploading(true);
    setUploadError("");
    const token = localStorage.getItem("token");
    if (!token) {
      setUploading(false);
      setUploadError("Session expired. Please login again.");
      router.push("/login");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_URL}/upload/invoice`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` },
        body: formData,
      });

      const contentType = res.headers.get("content-type") || "";
      const payload = contentType.includes("application/json")
        ? await res.json()
        : { detail: await res.text() };

      if (res.ok) {
        const data = payload;
        const newJob: Job = {
          job_id: data.job_id,
          status: "pending",
          file_name: file.name
        };
        setJobs((prev) => [newJob, ...prev]);
        startPolling(data.job_id);
        setFile(null);
        // Reset input safely using the cached element
        formElement.reset();
      } else {
        setUploadError(
          `Upload failed (${res.status}): ${payload.detail || "Unknown error"}`
        );
      }
    } catch (err) {
      setUploadError("Connection error. Ensure API Gateway is running on port 3000.");
    } finally {
      setUploading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem("token");
    router.push("/login");
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
      color: "#f8fafc",
      fontFamily: "'Inter', system-ui, sans-serif",
      padding: "40px 20px"
    }}>
      <div style={{ maxWidth: "800px", margin: "0 auto" }}>

        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "40px" }}>
          <h1 style={{ margin: 0, fontSize: "28px", fontWeight: "700", letterSpacing: "-0.5px", background: "linear-gradient(to right, #60a5fa, #a78bfa)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            Invoice Reconciler
          </h1>
          <button
            onClick={logout}
            style={{
              background: "rgba(255, 255, 255, 0.1)", border: "1px solid rgba(255, 255, 255, 0.2)",
              color: "#fff", padding: "8px 20px", borderRadius: "8px", fontWeight: "500",
              cursor: "pointer", transition: "all 0.2s ease", backdropFilter: "blur(10px)"
            }}
            onMouseOver={(e) => e.currentTarget.style.background = "rgba(255, 255, 255, 0.15)"}
            onMouseOut={(e) => e.currentTarget.style.background = "rgba(255, 255, 255, 0.1)"}
          >
            Logout
          </button>
        </div>

        {/* Upload Box */}
        <div style={{
          background: "rgba(30, 41, 59, 0.7)", backdropFilter: "blur(16px)",
          border: "1px solid rgba(255, 255, 255, 0.1)", borderRadius: "16px",
          padding: "30px", marginBottom: "40px", boxShadow: "0 10px 30px rgba(0,0,0,0.2)"
        }}>
          <h3 style={{ margin: "0 0 20px 0", color: "#e2e8f0", fontSize: "18px", fontWeight: "600" }}>Upload New Invoice</h3>
          <form onSubmit={handleUpload} style={{ display: "flex", gap: "15px", alignItems: "center", flexWrap: "wrap" }}>
            <input
              type="file"
              accept=".csv,.pdf"
              onChange={handleFileChange}
              required
              style={{
                padding: "12px", border: "1px solid rgba(255, 255, 255, 0.2)",
                borderRadius: "8px", flex: 1, background: "rgba(0,0,0,0.2)",
                color: "#f8fafc", outline: "none", minWidth: "250px"
              }}
            />
            <button
              type="submit"
              disabled={uploading || !file}
              style={{
                background: (uploading || !file) ? "#475569" : "linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)",
                border: "none", color: "#fff", padding: "12px 28px", borderRadius: "8px",
                fontWeight: "600", cursor: (uploading || !file) ? "not-allowed" : "pointer",
                transition: "transform 0.2s, box-shadow 0.2s",
                boxShadow: (uploading || !file) ? "none" : "0 4px 15px rgba(139, 92, 246, 0.4)"
              }}
              onMouseOver={(e) => { if (!uploading && file) { e.currentTarget.style.transform = "translateY(-2px)"; e.currentTarget.style.boxShadow = "0 6px 20px rgba(139, 92, 246, 0.6)"; } }}
              onMouseOut={(e) => { if (!uploading && file) { e.currentTarget.style.transform = "translateY(0)"; e.currentTarget.style.boxShadow = "0 4px 15px rgba(139, 92, 246, 0.4)"; } }}
            >
              {uploading ? "Uploading..." : "Process Invoice"}
            </button>
          </form>
          {uploadError && (
            <p style={{ color: "#ef4444", marginTop: "12px", fontSize: "14px", fontWeight: "500", display: "flex", alignItems: "center", gap: "6px" }}>
              <span style={{ fontSize: "16px" }}>⚠️</span> {uploadError}
            </p>
          )}
          <p style={{ fontSize: "13px", color: "#94a3b8", margin: "15px 0 0 0" }}>Supported formats: PDF, CSV</p>
        </div>

        {/* Jobs List */}
        <h2 style={{ fontSize: "22px", color: "#f8fafc", marginBottom: "20px", fontWeight: "600" }}>Processing Jobs</h2>
        {jobs.length === 0 && <p style={{ color: "#94a3b8", fontStyle: "italic", padding: "20px", background: "rgba(30,41,59,0.4)", borderRadius: "12px", textAlign: "center" }}>No jobs processed yet. Upload an invoice to start.</p>}

        {jobs.map((job) => (
          <div
            key={job.job_id}
            style={{
              background: "rgba(30, 41, 59, 0.6)",
              border: "1px solid rgba(255, 255, 255, 0.05)",
              borderRadius: "12px", padding: "20px", marginBottom: "16px",
              boxShadow: "0 4px 6px rgba(0,0,0,0.1)", transition: "transform 0.2s"
            }}
            onMouseOver={(e) => e.currentTarget.style.transform = "translateX(4px)"}
            onMouseOut={(e) => e.currentTarget.style.transform = "translateX(0)"}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
              <strong style={{ fontSize: "16px", color: "#f1f5f9" }}>{job.file_name}</strong>
              <span style={{
                fontWeight: "700", fontSize: "12px", padding: "4px 10px", borderRadius: "20px", letterSpacing: "0.5px",
                background: job.status === "completed" ? "rgba(16, 185, 129, 0.15)" : job.status === "failed" ? "rgba(239, 68, 68, 0.15)" : "rgba(245, 158, 11, 0.15)",
                color: job.status === "completed" ? "#10b981" : job.status === "failed" ? "#ef4444" : "#f59e0b"
              }}>
                {(job.status || "pending").toUpperCase()}
              </span>
            </div>
            <p style={{ fontSize: "12px", color: "#64748b", margin: "0 0 15px 0", fontFamily: "monospace" }}>ID: {job.job_id}</p>

            {job.status === "completed" && (
              <div style={{ marginTop: "15px", borderTop: "1px solid rgba(255, 255, 255, 0.08)", paddingTop: "15px" }}>
                <p style={{ margin: "0 0 10px 0" }}>
                  <strong style={{ color: "#cbd5e1" }}>Result: </strong>
                  {job.anomaly_flags && job.anomaly_flags.length > 0 ? (
                    <span style={{ color: "#ef4444", fontWeight: "600", background: "rgba(239, 68, 68, 0.1)", padding: "4px 8px", borderRadius: "6px" }}>⚠️ {job.anomaly_flags.join(", ")}</span>
                  ) : (
                    <span style={{ color: "#10b981", fontWeight: "600", background: "rgba(16, 185, 129, 0.1)", padding: "4px 8px", borderRadius: "6px" }}>✅ Clean (No Anomalies)</span>
                  )}
                </p>

                {job.mismatch_details && Object.keys(job.mismatch_details).length > 0 && (
                  <div style={{ background: "rgba(0, 0, 0, 0.2)", borderLeft: "3px solid #ef4444", padding: "12px 15px", borderRadius: "0 8px 8px 0", marginTop: "12px" }}>
                    <strong style={{ color: "#f8fafc", fontSize: "14px", display: "block", marginBottom: "8px" }}>Issues Found:</strong>
                    <ul style={{ margin: 0, paddingLeft: "20px", color: "#f1f5f9" }}>
                      {Object.entries(job.mismatch_details).map(([key, value]) => (
                        <li key={key} style={{ fontSize: "14px", marginBottom: "4px", lineHeight: "1.5" }}>{value as string}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {job.status === "failed" && (
              <p style={{ color: "#ef4444", fontSize: "14px", background: "rgba(239, 68, 68, 0.1)", padding: "10px", borderRadius: "8px", margin: "10px 0 0 0" }}>
                Error: {job.error || "Processing failed"}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}


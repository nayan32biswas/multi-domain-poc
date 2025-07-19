import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

import type { Project } from "../../types/project";
import { ApiService } from "../../services/api";

import "./style.css";

const Home: React.FC = () => {
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProject = async () => {
      try {
        setLoading(true);
        setError(null);
        const projectData = await ApiService.getProject();
        console.log("Fetched project data:", projectData);
        setProject(projectData);
      } catch (err) {
        setError("Failed to load project details. Please try again later.");
        console.error("Error fetching project:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchProject();
  }, []);

  const handleEditProject = () => {
    if (project) {
      navigate(`/projects/${project.id}/edit`);
    }
  };

  if (loading) {
    return (
      <div className="home-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading project details...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="home-container">
        <div className="error-state">
          <h2>Error Loading Project</h2>
          <p>{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="retry-button"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="home-container">
        <div className="error-state">
          <h2>Project Not Found</h2>
          <p>No project data available.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="home-container">
      <header className="project-header">
        <div className="project-title-section">
          <h1>{project.title}</h1>
        </div>
      </header>

      <main className="project-content">
        <section className="project-info">
          <h2>Project Information</h2>
          <div className="info-grid">
            <div className="info-item">
              <label>Project ID:</label>
              <span>{project.id}</span>
            </div>
            <div className="info-item">
              <label>SubDomain:</label>
              <span>{project.subdomain}</span>
            </div>
            <div className="info-item">
              <label>Custom Domain:</label>
              <span>{project.custom_domain}</span>
            </div>
            <div className="info-item">
              <label>Created Date:</label>
              <span>
                {new Date(project.created_at).toLocaleDateString("en-US", {
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                })}
              </span>
            </div>
          </div>
        </section>

        <section className="project-description">
          <h2>Description</h2>
          <p>{project.description}</p>
        </section>

        <section className="project-actions">
          <h2>Actions</h2>
          <div className="action-buttons">
            <button
              className="action-button primary"
              onClick={handleEditProject}
            >
              Edit Project
            </button>
            <button className="action-button secondary">View Tasks</button>
            <button className="action-button secondary">View Files</button>
            <button className="action-button secondary">Settings</button>
          </div>
        </section>
      </main>
    </div>
  );
};

export default Home;

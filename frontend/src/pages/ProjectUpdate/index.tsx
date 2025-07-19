import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";

import type { Project } from "../../types/project";
import { ApiService } from "../../services/api";

import "./style.css";

const ProjectUpdate: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    title: "",
    description: "",
  });
  const [errors, setErrors] = useState<{ [key: string]: string }>({});

  useEffect(() => {
    const fetchProject = async () => {
      try {
        setLoading(true);
        setError(null);
        const projectData = await ApiService.getProject();
        console.log("Fetched project data:", projectData);
        setProject(projectData);
        setFormData({
          title: projectData.title,
          description: projectData.description,
        });
      } catch (err) {
        setError("Failed to load project details. Please try again later.");
        console.error("Error fetching project:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchProject();
  }, [projectId]);

  const handleInputChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >
  ) => {
    const { name, value } = e.target;
    console.log(`Input changed: ${name} = ${value}`);
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors((prev) => ({
        ...prev,
        [name]: "",
      }));
    }
  };

  const validateForm = () => {
    const newErrors: { [key: string]: string } = {};

    if (!formData.title.trim()) {
      newErrors.title = "Project title is required";
    } else if (formData.title.trim().length < 3) {
      newErrors.title = "Project title must be at least 3 characters";
    }

    if (!formData.description.trim()) {
      newErrors.description = "Project description is required";
    } else if (formData.description.trim().length < 10) {
      newErrors.description =
        "Project description must be at least 10 characters";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!project) {
      setError("Project not found");
      return;
    }

    if (!validateForm()) {
      return;
    }

    setSaving(true);
    setError(null);

    try {
      // Use API to update project
      await ApiService.updateProject(project.id, {
        title: formData.title,
        description: formData.description,
      });

      // Navigate back to home page
      navigate("/");
    } catch (err) {
      console.error("Error updating project:", err);
      setError("Failed to update project. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    navigate("/");
  };

  if (loading) {
    return (
      <div className="project-update-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading project details...</p>
        </div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="project-update-container">
        <div className="error-state">
          <h2>Project Not Found</h2>
          <p>The project with ID "{projectId}" could not be found.</p>
          <button onClick={() => navigate("/")} className="back-button">
            ← Back to Home
          </button>
        </div>
      </div>
    );
  }

  console.log("forms ", formData);

  return (
    <div className="project-update-container">
      <nav className="breadcrumb">
        <button onClick={() => navigate("/")} className="back-link">
          ← Back to Home
        </button>
        <span className="breadcrumb-separator">/</span>
        <span className="breadcrumb-current">Edit Project</span>
      </nav>

      <header className="page-header">
        <h1>Edit Project</h1>
        <p>Update the project details below</p>
      </header>

      {error && (
        <div className="error-banner">
          <p>{error}</p>
          <button onClick={() => setError(null)} className="close-error">
            ×
          </button>
        </div>
      )}

      <main className="form-container">
        <form onSubmit={handleSubmit} className="project-form">
          <div className="form-group">
            <label htmlFor="title" className="form-label">
              Project Title *
            </label>
            <input
              type="text"
              id="title"
              name="title"
              value={formData.title}
              onChange={handleInputChange}
              className={`form-input ${errors.title ? "error" : ""}`}
              placeholder="Enter project title"
              disabled={saving}
            />
            {errors.title && (
              <span className="error-message">{errors.title}</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="description" className="form-label">
              Description *
            </label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              className={`form-textarea ${errors.description ? "error" : ""}`}
              placeholder="Enter project description"
              rows={4}
              disabled={saving}
            />
            {errors.description && (
              <span className="error-message">{errors.description}</span>
            )}
          </div>

          <div className="form-actions">
            <button
              type="button"
              onClick={handleCancel}
              className="cancel-button"
              disabled={saving}
            >
              Cancel
            </button>
            <button type="submit" className="submit-button" disabled={saving}>
              {saving ? (
                <>
                  <span className="button-spinner"></span>
                  Saving...
                </>
              ) : (
                "Save Changes"
              )}
            </button>
          </div>
        </form>
      </main>
    </div>
  );
};

export default ProjectUpdate;

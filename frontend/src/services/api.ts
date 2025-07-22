import { API_BASE_URL, SUBDOMAIN, CUSTOM_DOMAIN } from "../config";
import type { Project } from "../types/project";

const URLS = {
  projects: `${API_BASE_URL}/api/projects`,
  projectDetails: (id: string) => `${API_BASE_URL}/api/projects/${id}`,
};

const getHeaders = () => {
  const headers = {
    "Content-Type": "application/json",
    Accept: "application/json",
  } as Record<string, string>;

  if (SUBDOMAIN) {
    headers["X-Subdomain"] = SUBDOMAIN;
  }

  if (CUSTOM_DOMAIN) {
    headers["X-Custom-Domain"] = CUSTOM_DOMAIN;
  }

  return headers;
};

const handleApiResponse = async (response: Response) => {
  if (!response.ok) {
    const errorText = await response.text();
    let errorMessage = `HTTP error! status: ${response.status}`;

    try {
      const errorData = JSON.parse(errorText);
      if (errorData.detail) {
        errorMessage = errorData.detail;
      } else if (errorData.message) {
        errorMessage = errorData.message;
      }
    } catch {
      // If parsing fails, use the status text
      errorMessage = response.statusText || errorMessage;
    }

    throw new Error(errorMessage);
  }

  return response.json();
};

export class ApiService {
  // Fetch project details
  static async getProject(): Promise<Project> {
    try {
      const response = await fetch(URLS.projects, {
        method: "GET",
        headers: getHeaders(),
      });

      const projects = await handleApiResponse(response);

      return projects.results[0];
    } catch (error) {
      console.error("Error fetching project:", error);
      throw error;
    }
  }

  // Update project details
  static async updateProject(
    projectID: string,
    projectData: Partial<Project>
  ): Promise<Project> {
    try {
      const response = await fetch(URLS.projectDetails(projectID), {
        method: "PUT",
        headers: getHeaders(),
        body: JSON.stringify(projectData),
      });

      return await handleApiResponse(response);
    } catch (error) {
      console.error("Error updating project:", error);
      throw error;
    }
  }
}

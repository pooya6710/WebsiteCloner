import { apiRequest } from "./queryClient";

interface RepoData {
  repoUrl: string;
  branch: string;
  localPath: string;
  installDeps: boolean;
  envSetup: boolean;
}

export async function cloneRepository(repoData: RepoData) {
  try {
    const response = await apiRequest('POST', '/api/repositories/clone', repoData);
    return await response.json();
  } catch (error) {
    console.error('Error cloning repository:', error);
    throw error;
  }
}

export async function getRepositories() {
  try {
    const response = await fetch('/api/repositories', {
      credentials: 'include'
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch repositories');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching repositories:', error);
    throw error;
  }
}

export async function getRepositoryById(id: string) {
  try {
    const response = await fetch(`/api/repositories/${id}`, {
      credentials: 'include'
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch repository');
    }
    
    return await response.json();
  } catch (error) {
    console.error(`Error fetching repository ${id}:`, error);
    throw error;
  }
}

export async function executeRepositoryAction(repoId: string, action: string, options?: any) {
  try {
    const response = await apiRequest('POST', `/api/repositories/${repoId}/actions/${action}`, options);
    return await response.json();
  } catch (error) {
    console.error(`Error executing action ${action} on repository ${repoId}:`, error);
    throw error;
  }
}

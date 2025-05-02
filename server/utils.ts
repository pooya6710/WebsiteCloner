// Validate GitHub repository URL
export function validateRepositoryUrl(url: string): boolean {
  // Simple validation for GitHub URL
  const githubPattern = /^https?:\/\/(www\.)?github\.com\/[\w-]+\/[\w.-]+(\/?|\.git)?$/i;
  return githubPattern.test(url);
}

// Parse repository name from URL
export function parseRepoNameFromUrl(url: string): string {
  const parts = url.split('/');
  let name = parts[parts.length - 1];
  
  // Remove .git extension if present
  if (name.endsWith('.git')) {
    name = name.slice(0, -4);
  }
  
  return name;
}

// Generate mock repository statistics
export function generateMockStats() {
  return {
    linesOfCode: Math.floor(Math.random() * 20000) + 5000,
    files: Math.floor(Math.random() * 100) + 20,
  };
}

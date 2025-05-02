import { useState } from "react";
import RepositoryManager from "@/components/RepositoryManager";
import RepoDetails from "@/components/RepoDetails";

export default function Dashboard() {
  const [isCloning, setIsCloning] = useState(false);
  const [repoData, setRepoData] = useState({
    repoUrl: "https://github.com/username/my-fullstack-app",
    branch: "main",
    localPath: "/Users/developer/projects/my-fullstack-app",
    installDeps: true,
    envSetup: true
  });

  return (
    <div className="container mx-auto">
      {/* Page Header */}
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Repository Management</h2>
          <p className="text-gray-600">Clone, setup, and improve your GitHub repositories</p>
        </div>
        <div className="flex space-x-2">
          <button className="btn-outline">
            <i className="fas fa-filter mr-2"></i>
            Filter
          </button>
          <button className="btn-outline">
            <i className="fas fa-sort mr-2"></i>
            Sort
          </button>
        </div>
      </div>

      {/* Repository Manager */}
      <RepositoryManager 
        isCloning={isCloning} 
        setIsCloning={setIsCloning} 
        repoData={repoData}
        setRepoData={setRepoData}
      />

      {/* Repository Details */}
      <RepoDetails />
    </div>
  );
}

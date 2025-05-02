import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function RepoInfo() {
  const repoInfo = {
    name: "my-fullstack-app",
    owner: {
      username: "username",
      avatar: "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=120&q=80"
    },
    lastUpdated: "2 days ago",
    defaultBranch: "main",
    technologies: ["React", "Express", "JavaScript", "MongoDB"],
    stats: {
      linesOfCode: "12,543",
      files: "47"
    }
  };

  const getTechBadgeColor = (tech: string) => {
    switch (tech.toLowerCase()) {
      case 'react':
        return 'bg-blue-100 text-blue-800';
      case 'express':
        return 'bg-green-100 text-green-800';
      case 'javascript':
        return 'bg-yellow-100 text-yellow-800';
      case 'mongodb':
        return 'bg-purple-100 text-purple-800';
      case 'node.js':
        return 'bg-green-100 text-green-800';
      case 'typescript':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Card className="bg-white rounded-lg shadow-md p-6 mb-6">
      <CardContent className="p-0">
        <h3 className="text-xl font-semibold mb-4">Repository Info</h3>
        <div className="space-y-4">
          <div>
            <h4 className="text-sm text-gray-500 uppercase tracking-wider">Project</h4>
            <p className="font-medium">{repoInfo.name}</p>
          </div>
          <div>
            <h4 className="text-sm text-gray-500 uppercase tracking-wider">Owner</h4>
            <div className="flex items-center">
              <img 
                src={repoInfo.owner.avatar} 
                alt="Owner avatar" 
                className="w-6 h-6 rounded-full mr-2"
              />
              <span>{repoInfo.owner.username}</span>
            </div>
          </div>
          <div>
            <h4 className="text-sm text-gray-500 uppercase tracking-wider">Last Updated</h4>
            <p>{repoInfo.lastUpdated}</p>
          </div>
          <div>
            <h4 className="text-sm text-gray-500 uppercase tracking-wider">Default Branch</h4>
            <p>{repoInfo.defaultBranch}</p>
          </div>
          <div>
            <h4 className="text-sm text-gray-500 uppercase tracking-wider">Technologies</h4>
            <div className="flex flex-wrap gap-2 mt-1">
              {repoInfo.technologies.map((tech, idx) => (
                <Badge key={idx} variant="outline" className={getTechBadgeColor(tech)}>
                  {tech}
                </Badge>
              ))}
            </div>
          </div>
        </div>
        <div className="border-t border-gray-200 mt-4 pt-4">
          <h4 className="text-sm text-gray-500 uppercase tracking-wider mb-2">Statistics</h4>
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center">
              <div className="flex items-center justify-center h-10 w-10 rounded-full bg-blue-100 text-blue-800 mx-auto">
                <i className="fas fa-code"></i>
              </div>
              <div className="mt-2">
                <p className="text-lg font-semibold">{repoInfo.stats.linesOfCode}</p>
                <p className="text-xs text-gray-500">Lines of Code</p>
              </div>
            </div>
            <div className="text-center">
              <div className="flex items-center justify-center h-10 w-10 rounded-full bg-green-100 text-green-800 mx-auto">
                <i className="fas fa-file-code"></i>
              </div>
              <div className="mt-2">
                <p className="text-lg font-semibold">{repoInfo.stats.files}</p>
                <p className="text-xs text-gray-500">Files</p>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

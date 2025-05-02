import ImprovementPlan from "./ImprovementPlan";
import RepoInfo from "./RepoInfo";
import ActionCenter from "./ActionCenter";
import FileTree from "./FileTree";

export default function RepoDetails() {
  const folderStructure = [
    {
      name: "client",
      type: "folder",
      children: [
        { name: "public", type: "folder", children: [] },
        { 
          name: "src", 
          type: "folder", 
          children: [
            { name: "components", type: "folder", children: [] },
            { name: "pages", type: "folder", children: [] },
            { name: "App.js", type: "file", extension: "js" },
            { name: "index.js", type: "file", extension: "js" }
          ] 
        },
        { name: "package.json", type: "file", extension: "json" }
      ]
    },
    {
      name: "server",
      type: "folder",
      children: [
        { name: "controllers", type: "folder", children: [] },
        { name: "models", type: "folder", children: [] },
        { name: "routes", type: "folder", children: [] },
        { name: "server.js", type: "file", extension: "js" }
      ]
    },
    { name: ".env.example", type: "file", extension: "env" },
    { name: ".gitignore", type: "file", extension: "gitignore" },
    { name: "README.md", type: "file", extension: "md" },
    { name: "package.json", type: "file", extension: "json" }
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2">
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h3 className="text-xl font-semibold mb-4">Repository Structure</h3>
          <div className="border rounded-md">
            <div className="flex items-center justify-between bg-gray-50 p-3 border-b">
              <div className="flex items-center">
                <i className="fas fa-folder text-primary mr-2"></i>
                <span className="font-medium">my-fullstack-app</span>
              </div>
              <div>
                <button className="text-gray-500 hover:text-primary">
                  <i className="fas fa-expand"></i>
                </button>
              </div>
            </div>
            <div className="p-3 font-mono text-sm">
              <FileTree structure={folderStructure} />
            </div>
          </div>
        </div>

        <ImprovementPlan />
      </div>

      <div>
        <RepoInfo />
        <ActionCenter />
      </div>
    </div>
  );
}

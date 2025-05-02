import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function ActionCenter() {
  const handleAction = (action: string) => {
    // In a real app, these would trigger actual actions
    console.log(`Action triggered: ${action}`);
  };

  return (
    <Card className="bg-white rounded-lg shadow-md p-6">
      <CardContent className="p-0">
        <h3 className="text-xl font-semibold mb-4">Actions</h3>
        <div className="space-y-3">
          <Button 
            variant="ghost"
            className="w-full flex items-center justify-between px-4 py-3 bg-blue-50 text-blue-700 rounded-md hover:bg-blue-100 transition duration-200"
            onClick={() => handleAction('openTerminal')}
          >
            <div className="flex items-center">
              <i className="fas fa-terminal mr-3"></i>
              <span>Open Terminal</span>
            </div>
            <i className="fas fa-chevron-right"></i>
          </Button>
          <Button 
            variant="ghost"
            className="w-full flex items-center justify-between px-4 py-3 bg-purple-50 text-purple-700 rounded-md hover:bg-purple-100 transition duration-200"
            onClick={() => handleAction('openVSCode')}
          >
            <div className="flex items-center">
              <i className="fas fa-code mr-3"></i>
              <span>Open in VS Code</span>
            </div>
            <i className="fas fa-chevron-right"></i>
          </Button>
          <Button 
            variant="ghost"
            className="w-full flex items-center justify-between px-4 py-3 bg-green-50 text-green-700 rounded-md hover:bg-green-100 transition duration-200"
            onClick={() => handleAction('startDevServer')}
          >
            <div className="flex items-center">
              <i className="fas fa-play mr-3"></i>
              <span>Start Development Server</span>
            </div>
            <i className="fas fa-chevron-right"></i>
          </Button>
          <Button 
            variant="ghost"
            className="w-full flex items-center justify-between px-4 py-3 bg-orange-50 text-orange-700 rounded-md hover:bg-orange-100 transition duration-200"
            onClick={() => handleAction('runDiagnostics')}
          >
            <div className="flex items-center">
              <i className="fas fa-wrench mr-3"></i>
              <span>Run Diagnostics</span>
            </div>
            <i className="fas fa-chevron-right"></i>
          </Button>
        </div>
        <div className="mt-4 pt-4 border-t border-gray-200">
          <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="text-primary hover:text-blue-700 flex items-center">
            <i className="fas fa-external-link-alt mr-2"></i>
            <span>View on GitHub</span>
          </a>
        </div>
      </CardContent>
    </Card>
  );
}

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import CloneProgress from "./CloneProgress";
import { cloneRepository } from "@/lib/repoService";

interface RepositoryManagerProps {
  isCloning: boolean;
  setIsCloning: (isCloning: boolean) => void;
  repoData: {
    repoUrl: string;
    branch: string;
    localPath: string;
    installDeps: boolean;
    envSetup: boolean;
  };
  setRepoData: (data: any) => void;
}

export default function RepositoryManager({ 
  isCloning, 
  setIsCloning, 
  repoData, 
  setRepoData 
}: RepositoryManagerProps) {
  const { toast } = useToast();
  const [progress, setProgress] = useState({
    init: { status: 'pending', percent: 0 },
    download: { status: 'pending', percent: 0 },
    deps: { status: 'pending', percent: 0 },
    env: { status: 'pending', percent: 0 }
  });
  const [logOutput, setLogOutput] = useState("");

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setRepoData({
      ...repoData,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate form
    if (!repoData.repoUrl) {
      toast({
        title: "Error",
        description: "Repository URL is required",
        variant: "destructive"
      });
      return;
    }
    
    setIsCloning(true);
    
    // Update progress status as simulation
    // In a real app, this would be updated based on API responses
    setProgress({
      ...progress,
      init: { status: 'in-progress', percent: 0 }
    });
    
    // Simulate cloning process
    simulateCloneProcess();
    
    // In a real app, you would call the actual API and update progress
    // based on real responses
    try {
      const response = await cloneRepository(repoData);
      if (response.success) {
        toast({
          title: "Success",
          description: "Repository cloned successfully!",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to clone repository",
        variant: "destructive"
      });
      setIsCloning(false);
    }
  };
  
  // This is a simulation for demonstration purposes
  const simulateCloneProcess = () => {
    const steps = [
      { 
        stage: 'init', 
        duration: 2000, 
        log: "$ git clone " + repoData.repoUrl + "\nCloning into 'my-fullstack-app'...\n"
      },
      { 
        stage: 'download', 
        duration: 3000, 
        log: "remote: Enumerating objects: 265, done.\nremote: Counting objects: 100% (265/265), done.\nremote: Compressing objects: 100% (153/153), done.\nremote: Total 265 (delta 108), reused 245 (delta 98)\nReceiving objects: 100% (265/265), 58.25 KiB | 1.21 MiB/s, done.\nResolving deltas: 100% (108/108), done.\n\n"
      },
      { 
        stage: 'deps', 
        duration: 5000, 
        log: "$ cd my-fullstack-app\n$ npm install\nadded 1257 packages, and audited 1258 packages in 25s\n103 packages are looking for funding\n  run `npm fund` for details\nfound 0 vulnerabilities\n"
      },
      { 
        stage: 'env', 
        duration: 2000, 
        log: "$ cp .env.example .env\n$ Setting up environment variables\nEnvironment setup complete!\n"
      }
    ];
    
    let currentLog = "";
    
    steps.forEach((step, index) => {
      setTimeout(() => {
        // Update progress for current step
        const updatedProgress = {...progress};
        updatedProgress[step.stage as keyof typeof progress].status = 'in-progress';
        updatedProgress[step.stage as keyof typeof progress].percent = 0;
        setProgress(updatedProgress);
        
        // Start progress animation
        let percent = 0;
        const progressInterval = setInterval(() => {
          percent += 5;
          const newProgress = {...updatedProgress};
          newProgress[step.stage as keyof typeof progress].percent = Math.min(percent, 100);
          setProgress(newProgress);
          
          // Update log
          currentLog += step.log.slice(0, percent / 2);
          setLogOutput(currentLog);
          
          if (percent >= 100) {
            clearInterval(progressInterval);
            
            // Mark step as completed
            const completedProgress = {...newProgress};
            completedProgress[step.stage as keyof typeof progress].status = 'completed';
            setProgress(completedProgress);
            
            // If this is the last step, finish the process
            if (index === steps.length - 1) {
              setTimeout(() => {
                setIsCloning(false);
              }, 1000);
            }
          }
        }, step.duration / 20);
      }, steps.slice(0, index).reduce((sum, s) => sum + s.duration, 0));
    });
  };

  return (
    <Card className="bg-white rounded-lg shadow-md p-6 mb-6">
      <CardContent className="p-0">
        <div className="flex items-center mb-4">
          <div className="bg-primary bg-opacity-10 p-3 rounded-full">
            <i className="fas fa-code-branch text-primary text-xl"></i>
          </div>
          <div className="ml-4">
            <h3 className="text-xl font-semibold">Clone GitHub Repository</h3>
            <p className="text-gray-600">Enter repository details to clone and set up locally</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <Label htmlFor="repoUrl" className="text-sm font-medium text-gray-700 mb-1">Repository URL</Label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <i className="fas fa-link text-gray-400"></i>
                </div>
                <Input 
                  type="text" 
                  id="repoUrl" 
                  name="repoUrl" 
                  className="pl-10 pr-12"
                  placeholder="https://github.com/username/repo" 
                  value={repoData.repoUrl}
                  onChange={handleInputChange}
                />
              </div>
            </div>
            <div>
              <Label htmlFor="branch" className="text-sm font-medium text-gray-700 mb-1">Branch (Optional)</Label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <i className="fas fa-code-branch text-gray-400"></i>
                </div>
                <Input 
                  type="text" 
                  id="branch" 
                  name="branch" 
                  className="pl-10"
                  placeholder="main" 
                  value={repoData.branch}
                  onChange={handleInputChange}
                />
              </div>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <Label htmlFor="localPath" className="text-sm font-medium text-gray-700 mb-1">Local Directory</Label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <i className="fas fa-folder text-gray-400"></i>
                </div>
                <Input 
                  type="text" 
                  id="localPath" 
                  name="localPath" 
                  className="pl-10"
                  placeholder="/path/to/directory" 
                  value={repoData.localPath}
                  onChange={handleInputChange}
                />
                <div className="absolute inset-y-0 right-0 flex py-1.5 pr-1.5">
                  <Button type="button" variant="outline" size="sm" className="h-7 border border-gray-200 rounded px-2 text-sm text-gray-600 hover:bg-gray-100">
                    Browse
                  </Button>
                </div>
              </div>
            </div>
            <div>
              <Label className="text-sm font-medium text-gray-700 mb-1 block">Setup Options</Label>
              <div className="mt-1 space-y-2">
                <div className="flex items-center">
                  <Checkbox 
                    id="installDeps" 
                    name="installDeps" 
                    checked={repoData.installDeps}
                    onCheckedChange={(checked) => 
                      setRepoData({...repoData, installDeps: !!checked})
                    }
                  />
                  <Label htmlFor="installDeps" className="ml-2 text-sm text-gray-700">Install dependencies</Label>
                </div>
                <div className="flex items-center">
                  <Checkbox 
                    id="envSetup" 
                    name="envSetup" 
                    checked={repoData.envSetup}
                    onCheckedChange={(checked) => 
                      setRepoData({...repoData, envSetup: !!checked})
                    }
                  />
                  <Label htmlFor="envSetup" className="ml-2 text-sm text-gray-700">Set up environment files</Label>
                </div>
              </div>
            </div>
          </div>
          <div className="flex justify-end mt-4">
            <Button 
              type="submit" 
              className="inline-flex items-center px-4 py-2 bg-primary hover:bg-blue-700 text-white"
              disabled={isCloning}
            >
              <i className="fas fa-download mr-2"></i>
              Clone Repository
            </Button>
          </div>
        </form>

        {/* Show Clone Progress when cloning */}
        {isCloning && (
          <CloneProgress 
            progress={progress}
            logOutput={logOutput}
          />
        )}
      </CardContent>
    </Card>
  );
}

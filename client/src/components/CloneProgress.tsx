import { Progress } from "@/components/ui/progress";

interface ProgressStep {
  status: 'pending' | 'in-progress' | 'completed';
  percent: number;
}

interface CloneProgressProps {
  progress: {
    init: ProgressStep;
    download: ProgressStep;
    deps: ProgressStep;
    env: ProgressStep;
  };
  logOutput: string;
}

export default function CloneProgress({ progress, logOutput }: CloneProgressProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <i className="fas fa-check-circle text-green-500"></i>;
      case 'in-progress':
        return <i className="fas fa-spinner fa-spin text-primary"></i>;
      default:
        return <i className="fas fa-circle text-gray-300"></i>;
    }
  };

  const getStatusText = (status: string, percent: number) => {
    switch (status) {
      case 'completed':
        return 'Completed';
      case 'in-progress':
        return `In progress (${percent}%)`;
      default:
        return 'Pending';
    }
  };

  const getProgressColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500';
      case 'in-progress':
        return 'bg-primary';
      default:
        return 'bg-gray-300';
    }
  };

  return (
    <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
      <h4 className="font-medium text-gray-700 mb-3">Clone Progress</h4>
      <div className="space-y-4">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            {getStatusIcon(progress.init.status)}
          </div>
          <div className="ml-3 flex-1">
            <div className="flex justify-between items-center mb-1">
              <span className="text-sm font-medium">Initializing clone</span>
              <span className="text-sm text-gray-500">{getStatusText(progress.init.status, progress.init.percent)}</span>
            </div>
            <Progress value={progress.init.percent} className="h-1.5 bg-gray-200">
              <div className={`${getProgressColor(progress.init.status)} h-1.5 rounded-full`} 
                   style={{ width: `${progress.init.percent}%` }}></div>
            </Progress>
          </div>
        </div>
        
        <div className="flex items-center">
          <div className="flex-shrink-0">
            {getStatusIcon(progress.download.status)}
          </div>
          <div className="ml-3 flex-1">
            <div className="flex justify-between items-center mb-1">
              <span className="text-sm font-medium">Downloading repository</span>
              <span className="text-sm text-gray-500">{getStatusText(progress.download.status, progress.download.percent)}</span>
            </div>
            <Progress value={progress.download.percent} className="h-1.5 bg-gray-200">
              <div className={`${getProgressColor(progress.download.status)} h-1.5 rounded-full`} 
                   style={{ width: `${progress.download.percent}%` }}></div>
            </Progress>
          </div>
        </div>
        
        <div className="flex items-center">
          <div className="flex-shrink-0">
            {getStatusIcon(progress.deps.status)}
          </div>
          <div className="ml-3 flex-1">
            <div className="flex justify-between items-center mb-1">
              <span className="text-sm font-medium">Installing dependencies</span>
              <span className="text-sm text-gray-500">{getStatusText(progress.deps.status, progress.deps.percent)}</span>
            </div>
            <Progress value={progress.deps.percent} className="h-1.5 bg-gray-200">
              <div className={`${getProgressColor(progress.deps.status)} h-1.5 rounded-full`} 
                   style={{ width: `${progress.deps.percent}%` }}></div>
            </Progress>
          </div>
        </div>
        
        <div className="flex items-center">
          <div className="flex-shrink-0">
            {getStatusIcon(progress.env.status)}
          </div>
          <div className="ml-3 flex-1">
            <div className="flex justify-between items-center mb-1">
              <span className="text-sm font-medium">Setting up environment</span>
              <span className="text-sm text-gray-500">{getStatusText(progress.env.status, progress.env.percent)}</span>
            </div>
            <Progress value={progress.env.percent} className="h-1.5 bg-gray-200">
              <div className={`${getProgressColor(progress.env.status)} h-1.5 rounded-full`} 
                   style={{ width: `${progress.env.percent}%` }}></div>
            </Progress>
          </div>
        </div>
      </div>
      
      <div className="mt-4 border border-gray-200 bg-black rounded-md text-white p-3 font-mono text-sm overflow-auto h-36">
        <div className="whitespace-pre-wrap">{logOutput}</div>
      </div>
    </div>
  );
}

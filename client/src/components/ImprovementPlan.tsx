import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface ImprovementTask {
  id: string;
  title: string;
  description: string;
  tags: string[];
  completed: boolean;
}

export default function ImprovementPlan() {
  const [tasks, setTasks] = useState<ImprovementTask[]>([
    {
      id: "enhance-1",
      title: "Optimize Frontend Performance",
      description: "Implement React.memo(), useCallback() and code splitting to improve rendering performance.",
      tags: ["React", "Performance"],
      completed: false
    },
    {
      id: "enhance-2",
      title: "Add API Request Caching",
      description: "Implement an efficient caching layer for API requests to reduce server load and improve responsiveness.",
      tags: ["Express", "Backend"],
      completed: false
    },
    {
      id: "enhance-3",
      title: "Implement Authentication System",
      description: "Add JWT-based user authentication with role management and secure password handling.",
      tags: ["Security", "Full Stack"],
      completed: false
    },
    {
      id: "enhance-4",
      title: "Set Up Automated Testing",
      description: "Configure Jest and React Testing Library for frontend, and Mocha/Chai for backend API tests.",
      tags: ["Testing", "CI/CD"],
      completed: false
    },
  ]);

  const handleCheckboxChange = (id: string, checked: boolean) => {
    setTasks(tasks.map(task => 
      task.id === id ? { ...task, completed: checked } : task
    ));
  };

  const handleAddTask = () => {
    // In a real app, this would open a modal to create a new task
    console.log("Add new task");
  };

  const getTagColor = (tag: string) => {
    switch (tag.toLowerCase()) {
      case 'react':
        return 'bg-blue-100 text-blue-800';
      case 'performance':
        return 'bg-yellow-100 text-yellow-800';
      case 'express':
        return 'bg-green-100 text-green-800';
      case 'backend':
        return 'bg-purple-100 text-purple-800';
      case 'security':
        return 'bg-red-100 text-red-800';
      case 'testing':
        return 'bg-indigo-100 text-indigo-800';
      case 'ci/cd':
        return 'bg-gray-100 text-gray-800';
      case 'full stack':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Card className="bg-white rounded-lg shadow-md p-6">
      <CardContent className="p-0">
        <h3 className="text-xl font-semibold mb-4">Improvement Plan</h3>
        <div className="space-y-4">
          {tasks.map((task, idx) => (
            <div key={task.id} className={idx > 0 ? "border-t border-gray-200 pt-4 flex items-start" : "flex items-start"}>
              <div className="mt-1 mr-3">
                <Checkbox 
                  id={task.id} 
                  checked={task.completed}
                  onCheckedChange={(checked) => handleCheckboxChange(task.id, !!checked)}
                />
              </div>
              <div>
                <label htmlFor={task.id} className="font-medium text-gray-700 block">{task.title}</label>
                <p className="text-gray-600 text-sm">{task.description}</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {task.tags.map((tag, i) => (
                    <Badge key={i} variant="outline" className={getTagColor(tag)}>
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          ))}
          <div className="mt-4">
            <Button variant="outline" size="sm" onClick={handleAddTask}>
              <i className="fas fa-plus mr-2"></i>
              Add Improvement Task
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

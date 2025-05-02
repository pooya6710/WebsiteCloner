import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { z } from "zod";
import { validateRepositoryUrl } from "./utils";

export async function registerRoutes(app: Express): Promise<Server> {
  // API routes for repository management
  
  // Get all repositories
  app.get('/api/repositories', async (req, res) => {
    try {
      const repositories = await storage.getAllRepositories();
      res.json(repositories);
    } catch (error) {
      console.error('Error fetching repositories:', error);
      res.status(500).json({ error: 'Failed to fetch repositories' });
    }
  });

  // Get repository by ID
  app.get('/api/repositories/:id', async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      if (isNaN(id)) {
        return res.status(400).json({ error: 'Invalid repository ID' });
      }

      const repository = await storage.getRepositoryById(id);
      if (!repository) {
        return res.status(404).json({ error: 'Repository not found' });
      }

      res.json(repository);
    } catch (error) {
      console.error(`Error fetching repository ${req.params.id}:`, error);
      res.status(500).json({ error: 'Failed to fetch repository' });
    }
  });

  // Clone repository
  app.post('/api/repositories/clone', async (req, res) => {
    try {
      // Validate request body
      const cloneSchema = z.object({
        repoUrl: z.string().min(1, 'Repository URL is required').refine(
          val => validateRepositoryUrl(val),
          'Invalid repository URL'
        ),
        branch: z.string().optional(),
        localPath: z.string().optional(),
        installDeps: z.boolean().optional(),
        envSetup: z.boolean().optional(),
      });

      const validatedData = cloneSchema.parse(req.body);
      
      // Extract repository name from URL
      const urlParts = validatedData.repoUrl.split('/');
      const repoName = urlParts[urlParts.length - 1].replace('.git', '');
      
      // In a real app, this would initiate the actual cloning process
      // Here we're simulating it by creating a record in the database
      const newRepository = await storage.createRepository({
        name: repoName,
        url: validatedData.repoUrl,
        branch: validatedData.branch || 'main',
        localPath: validatedData.localPath || `/default/path/${repoName}`,
        technologies: ['React', 'Express', 'JavaScript', 'MongoDB'],
        statistics: {
          linesOfCode: Math.floor(Math.random() * 20000) + 5000,
          files: Math.floor(Math.random() * 100) + 20,
        },
        ownerId: 1, // Default user ID, in a real app this would be the authenticated user
      });

      // Create a default improvement plan for this repository
      const improvementPlan = await storage.createImprovementPlan(newRepository.id);
      
      // Add some default improvement tasks
      const defaultTasks = [
        {
          title: 'Optimize Frontend Performance',
          description: 'Implement React.memo(), useCallback() and code splitting to improve rendering performance.',
          tags: ['React', 'Performance'],
          completed: false,
          planId: improvementPlan.id,
        },
        {
          title: 'Add API Request Caching',
          description: 'Implement an efficient caching layer for API requests to reduce server load and improve responsiveness.',
          tags: ['Express', 'Backend'],
          completed: false,
          planId: improvementPlan.id,
        },
        {
          title: 'Implement Authentication System',
          description: 'Add JWT-based user authentication with role management and secure password handling.',
          tags: ['Security', 'Full Stack'],
          completed: false,
          planId: improvementPlan.id,
        },
        {
          title: 'Set Up Automated Testing',
          description: 'Configure Jest and React Testing Library for frontend, and Mocha/Chai for backend API tests.',
          tags: ['Testing', 'CI/CD'],
          completed: false,
          planId: improvementPlan.id,
        },
      ];

      for (const task of defaultTasks) {
        await storage.createImprovementTask(task);
      }

      res.status(201).json({ 
        success: true, 
        message: 'Repository cloned successfully',
        repository: newRepository
      });
    } catch (error) {
      console.error('Error cloning repository:', error);
      if (error instanceof z.ZodError) {
        return res.status(400).json({ errors: error.errors });
      }
      res.status(500).json({ error: 'Failed to clone repository' });
    }
  });

  // Get improvement plan for a repository
  app.get('/api/repositories/:id/improvement-plan', async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      if (isNaN(id)) {
        return res.status(400).json({ error: 'Invalid repository ID' });
      }

      const improvementPlan = await storage.getImprovementPlanByRepositoryId(id);
      if (!improvementPlan) {
        return res.status(404).json({ error: 'Improvement plan not found' });
      }

      const tasks = await storage.getImprovementTasksByPlanId(improvementPlan.id);
      
      res.json({
        plan: improvementPlan,
        tasks
      });
    } catch (error) {
      console.error(`Error fetching improvement plan for repository ${req.params.id}:`, error);
      res.status(500).json({ error: 'Failed to fetch improvement plan' });
    }
  });

  // Update improvement task status
  app.patch('/api/improvement-tasks/:id', async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      if (isNaN(id)) {
        return res.status(400).json({ error: 'Invalid task ID' });
      }

      const updateSchema = z.object({
        completed: z.boolean(),
      });

      const validatedData = updateSchema.parse(req.body);
      
      const updatedTask = await storage.updateImprovementTask(id, validatedData);
      if (!updatedTask) {
        return res.status(404).json({ error: 'Task not found' });
      }

      res.json(updatedTask);
    } catch (error) {
      console.error(`Error updating task ${req.params.id}:`, error);
      if (error instanceof z.ZodError) {
        return res.status(400).json({ errors: error.errors });
      }
      res.status(500).json({ error: 'Failed to update task' });
    }
  });

  // Create a new improvement task
  app.post('/api/improvement-tasks', async (req, res) => {
    try {
      const taskSchema = z.object({
        planId: z.number(),
        title: z.string().min(1, 'Title is required'),
        description: z.string().optional(),
        tags: z.array(z.string()).optional(),
        completed: z.boolean().optional(),
      });

      const validatedData = taskSchema.parse(req.body);
      
      const newTask = await storage.createImprovementTask({
        ...validatedData,
        tags: validatedData.tags || [],
        completed: validatedData.completed || false,
      });

      res.status(201).json(newTask);
    } catch (error) {
      console.error('Error creating task:', error);
      if (error instanceof z.ZodError) {
        return res.status(400).json({ errors: error.errors });
      }
      res.status(500).json({ error: 'Failed to create task' });
    }
  });

  // Execute repository action
  app.post('/api/repositories/:id/actions/:action', async (req, res) => {
    try {
      const id = parseInt(req.params.id);
      if (isNaN(id)) {
        return res.status(400).json({ error: 'Invalid repository ID' });
      }

      const { action } = req.params;
      const validActions = ['openTerminal', 'openVSCode', 'startDevServer', 'runDiagnostics'];
      
      if (!validActions.includes(action)) {
        return res.status(400).json({ error: 'Invalid action' });
      }

      // In a real app, this would execute the actual action
      // Here we're just simulating a success response
      res.json({
        success: true,
        message: `Action ${action} executed successfully on repository ${id}`,
        data: {
          action,
          repositoryId: id,
          timestamp: new Date().toISOString(),
        }
      });
    } catch (error) {
      console.error(`Error executing action ${req.params.action} on repository ${req.params.id}:`, error);
      res.status(500).json({ error: 'Failed to execute action' });
    }
  });

  const httpServer = createServer(app);
  return httpServer;
}

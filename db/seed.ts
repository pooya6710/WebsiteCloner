import { db } from "./index";
import * as schema from "@shared/schema";
import { eq } from "drizzle-orm";

async function seed() {
  try {
    console.log("Starting database seed...");

    // Check if users table is empty
    const existingUsers = await db.query.users.findMany({ limit: 1 });
    
    if (existingUsers.length === 0) {
      console.log("Seeding users...");
      // Create default user
      const [user] = await db.insert(schema.users).values({
        username: "developer",
        password: "password123" // In a real app, this would be hashed
      }).returning();
      
      console.log(`Created user: ${user.username}`);
      
      // Seed some sample repositories
      const repositories = [
        {
          name: "my-fullstack-app",
          url: "https://github.com/username/my-fullstack-app",
          branch: "main",
          localPath: "/Users/developer/projects/my-fullstack-app",
          technologies: ["React", "Express", "JavaScript", "MongoDB"],
          statistics: { linesOfCode: 12543, files: 47 },
          ownerId: user.id
        },
        {
          name: "e-commerce-platform",
          url: "https://github.com/username/e-commerce-platform",
          branch: "main",
          localPath: "/Users/developer/projects/e-commerce-platform",
          technologies: ["Next.js", "Node.js", "TypeScript", "PostgreSQL"],
          statistics: { linesOfCode: 24786, files: 89 },
          ownerId: user.id
        },
        {
          name: "recipe-finder-app",
          url: "https://github.com/username/recipe-finder-app",
          branch: "develop",
          localPath: "/Users/developer/projects/recipe-finder-app",
          technologies: ["Vue.js", "Firebase", "JavaScript"],
          statistics: { linesOfCode: 8432, files: 35 },
          ownerId: user.id
        }
      ];
      
      console.log("Seeding repositories...");
      for (const repo of repositories) {
        const [createdRepo] = await db.insert(schema.repositories)
          .values(repo)
          .returning();
        
        console.log(`Created repository: ${createdRepo.name}`);
        
        // Create improvement plan for each repository
        const [plan] = await db.insert(schema.improvementPlans)
          .values({ repositoryId: createdRepo.id })
          .returning();
        
        console.log(`Created improvement plan for: ${createdRepo.name}`);
        
        // Create improvement tasks for each plan
        const tasks = [
          {
            title: "Optimize Frontend Performance",
            description: "Implement React.memo(), useCallback() and code splitting to improve rendering performance.",
            tags: ["React", "Performance"],
            completed: false,
            planId: plan.id
          },
          {
            title: "Add API Request Caching",
            description: "Implement an efficient caching layer for API requests to reduce server load and improve responsiveness.",
            tags: ["Express", "Backend"],
            completed: false,
            planId: plan.id
          },
          {
            title: "Implement Authentication System",
            description: "Add JWT-based user authentication with role management and secure password handling.",
            tags: ["Security", "Full Stack"],
            completed: createdRepo.id === 1, // First repo has this task completed
            planId: plan.id
          },
          {
            title: "Set Up Automated Testing",
            description: "Configure Jest and React Testing Library for frontend, and Mocha/Chai for backend API tests.",
            tags: ["Testing", "CI/CD"],
            completed: false,
            planId: plan.id
          }
        ];
        
        for (const task of tasks) {
          await db.insert(schema.improvementTasks)
            .values(task)
            .returning();
        }
        
        console.log(`Created improvement tasks for: ${createdRepo.name}`);
      }
    } else {
      console.log("Database already has users, skipping seed");
    }
    
    console.log("Database seed completed successfully!");
  } catch (error) {
    console.error("Error seeding database:", error);
  }
}

seed();

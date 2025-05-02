import { db } from '@db';
import { 
  repositories, 
  improvementPlans, 
  improvementTasks,
  Repository,
  InsertRepository,
  ImprovementTask,
  InsertImprovementTask
} from '@shared/schema';
import { eq } from 'drizzle-orm';

// Repository operations
export const getAllRepositories = async () => {
  return await db.query.repositories.findMany();
};

export const getRepositoryById = async (id: number) => {
  return await db.query.repositories.findFirst({
    where: eq(repositories.id, id)
  });
};

export const createRepository = async (data: InsertRepository) => {
  const [repository] = await db.insert(repositories).values(data).returning();
  return repository;
};

export const deleteRepository = async (id: number) => {
  return await db.delete(repositories).where(eq(repositories.id, id)).returning();
};

// Improvement plan operations
export const createImprovementPlan = async (repositoryId: number) => {
  const [plan] = await db.insert(improvementPlans).values({
    repositoryId
  }).returning();
  return plan;
};

export const getImprovementPlanByRepositoryId = async (repositoryId: number) => {
  return await db.query.improvementPlans.findFirst({
    where: eq(improvementPlans.repositoryId, repositoryId)
  });
};

// Improvement task operations
export const getImprovementTasksByPlanId = async (planId: number) => {
  return await db.query.improvementTasks.findMany({
    where: eq(improvementTasks.planId, planId)
  });
};

export const createImprovementTask = async (data: InsertImprovementTask) => {
  const [task] = await db.insert(improvementTasks).values(data).returning();
  return task;
};

export const updateImprovementTask = async (id: number, data: Partial<ImprovementTask>) => {
  const [updatedTask] = await db.update(improvementTasks)
    .set(data)
    .where(eq(improvementTasks.id, id))
    .returning();
  return updatedTask;
};

export const deleteImprovementTask = async (id: number) => {
  return await db.delete(improvementTasks).where(eq(improvementTasks.id, id)).returning();
};

export const storage = {
  getAllRepositories,
  getRepositoryById,
  createRepository,
  deleteRepository,
  createImprovementPlan,
  getImprovementPlanByRepositoryId,
  getImprovementTasksByPlanId,
  createImprovementTask,
  updateImprovementTask,
  deleteImprovementTask
};

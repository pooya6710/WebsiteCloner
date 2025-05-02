import { pgTable, text, serial, integer, boolean, timestamp, jsonb } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";
import { relations } from "drizzle-orm";

// Original user table - kept as-is
export const users = pgTable("users", {
  id: serial("id").primaryKey(),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
});

export const insertUserSchema = createInsertSchema(users).pick({
  username: true,
  password: true,
});

export type InsertUser = z.infer<typeof insertUserSchema>;
export type User = typeof users.$inferSelect;

// New tables for repository management
export const repositories = pgTable("repositories", {
  id: serial("id").primaryKey(),
  name: text("name").notNull(),
  url: text("url").notNull(),
  branch: text("branch").default("main"),
  localPath: text("local_path"),
  clonedAt: timestamp("cloned_at").defaultNow(),
  lastUpdatedAt: timestamp("last_updated_at").defaultNow(),
  ownerId: integer("owner_id").references(() => users.id),
  technologies: jsonb("technologies").$type<string[]>(),
  statistics: jsonb("statistics").$type<{ linesOfCode: number, files: number }>(),
});

export const repositoriesRelations = relations(repositories, ({ one }) => ({
  owner: one(users, {
    fields: [repositories.ownerId],
    references: [users.id],
  }),
  improvements: one(improvementPlans, {
    fields: [repositories.id],
    references: [improvementPlans.repositoryId],
  }),
}));

export const improvementPlans = pgTable("improvement_plans", {
  id: serial("id").primaryKey(),
  repositoryId: integer("repository_id").references(() => repositories.id).notNull(),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

export const improvementPlansRelations = relations(improvementPlans, ({ one, many }) => ({
  repository: one(repositories, {
    fields: [improvementPlans.repositoryId],
    references: [repositories.id],
  }),
  tasks: many(improvementTasks),
}));

export const improvementTasks = pgTable("improvement_tasks", {
  id: serial("id").primaryKey(),
  planId: integer("plan_id").references(() => improvementPlans.id).notNull(),
  title: text("title").notNull(),
  description: text("description"),
  tags: jsonb("tags").$type<string[]>(),
  completed: boolean("completed").default(false),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

export const improvementTasksRelations = relations(improvementTasks, ({ one }) => ({
  plan: one(improvementPlans, {
    fields: [improvementTasks.planId],
    references: [improvementPlans.id],
  }),
}));

// Insert/Select schemas
export const insertRepositorySchema = createInsertSchema(repositories, {
  name: (schema) => schema.min(1, "Repository name is required"),
  url: (schema) => schema.min(1, "Repository URL is required")
});

export const insertImprovementTaskSchema = createInsertSchema(improvementTasks, {
  title: (schema) => schema.min(1, "Task title is required"),
  planId: (schema) => schema.min(1, "Plan ID is required"),
});

export type InsertRepository = z.infer<typeof insertRepositorySchema>;
export type Repository = typeof repositories.$inferSelect;

export type InsertImprovementTask = z.infer<typeof insertImprovementTaskSchema>;
export type ImprovementTask = typeof improvementTasks.$inferSelect;

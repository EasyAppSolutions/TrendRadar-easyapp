// Example Prisma Client setup for Next.js
// Copy this to your Next.js project's lib/prisma.ts

import { PrismaClient } from '@prisma/client'
import { PrismaPg } from '@prisma/adapter-pg'
import { Pool } from 'pg'

// Create connection pool
const connectionString = process.env.DATABASE_URL
const pool = new Pool({ connectionString })
const adapter = new PrismaPg(pool)

// Prevent multiple instances in development
const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined
}

export const prisma =
  globalForPrisma.prisma ??
  new PrismaClient({
    adapter,
  })

if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = prisma

export default prisma

// ============================================================================
// Example Usage in Next.js API Routes or Server Components
// ============================================================================

/*
// Get today's headlines
import prisma from '@/lib/prisma'

export async function getTodayHeadlines() {
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  return prisma.headline.findMany({
    where: {
      firstSeenAt: { gte: today }
    },
    include: {
      source: true,
      occurrences: {
        orderBy: { crawledAt: 'desc' },
        take: 10
      }
    },
    orderBy: { lastSeenAt: 'desc' }
  })
}

// Get headlines by keyword
export async function searchHeadlines(keyword: string) {
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  return prisma.headline.findMany({
    where: {
      title: { contains: keyword, mode: 'insensitive' },
      firstSeenAt: { gte: today }
    },
    include: { source: true }
  })
}

// Get headlines grouped by source
export async function getHeadlinesBySource() {
  return prisma.source.findMany({
    where: { isActive: true },
    include: {
      headlines: {
        where: {
          firstSeenAt: { gte: new Date(Date.now() - 24 * 60 * 60 * 1000) }
        },
        orderBy: { lastSeenAt: 'desc' },
        take: 50
      }
    }
  })
}

// Get crawl session history
export async function getCrawlSessions(limit = 10) {
  return prisma.crawlSession.findMany({
    orderBy: { startedAt: 'desc' },
    take: limit
  })
}
*/

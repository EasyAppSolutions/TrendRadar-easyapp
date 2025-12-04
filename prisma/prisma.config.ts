import path from 'node:path'
import type { PrismaConfig } from 'prisma'

export default {
  earlyAccess: true,
  schema: path.join(__dirname, 'schema.prisma'),

  migrate: {
    async adapter() {
      const { PrismaPg } = await import('@prisma/adapter-pg')
      const { Pool } = await import('pg')

      const connectionString = process.env.DATABASE_URL

      const pool = new Pool({ connectionString })
      return new PrismaPg(pool)
    },
  },
} satisfies PrismaConfig

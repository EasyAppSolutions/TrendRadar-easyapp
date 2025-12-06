import { NextResponse } from "next/server";
import prisma from "@/lib/prisma";

export async function GET() {
  try {
    // Get headlines from last 24 hours
    const since = new Date(Date.now() - 24 * 60 * 60 * 1000);

    const headlines = await prisma.headline.findMany({
      where: {
        firstSeenAt: { gte: since },
      },
      include: {
        source: true,
        occurrences: {
          orderBy: { crawledAt: "desc" },
          take: 5,
        },
      },
      orderBy: { lastSeenAt: "desc" },
      take: 100,
    });

    // Group by source
    const bySource = headlines.reduce(
      (acc, headline) => {
        const sourceName = headline.source.platformName;
        if (!acc[sourceName]) {
          acc[sourceName] = [];
        }
        acc[sourceName].push({
          id: headline.id,
          title: headline.title,
          url: headline.url,
          mobileUrl: headline.mobileUrl,
          firstSeenAt: headline.firstSeenAt,
          lastSeenAt: headline.lastSeenAt,
          ranks: headline.occurrences.map((o) => o.rank),
        });
        return acc;
      },
      {} as Record<string, unknown[]>
    );

    return NextResponse.json({
      success: true,
      count: headlines.length,
      data: bySource,
    });
  } catch (error) {
    console.error("Database error:", error);
    return NextResponse.json(
      { success: false, error: "Failed to fetch headlines" },
      { status: 500 }
    );
  }
}

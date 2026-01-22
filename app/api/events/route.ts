import { NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';
import { DatabaseEvent, DisplayEvent, transformEvent } from '@/app/types/event';

export async function GET() {
  try {
    // Read the events JSON file
    const filePath = path.join(process.cwd(), 'data', 'events.json');
    const fileContents = await fs.readFile(filePath, 'utf-8');
    const rawEvents: DatabaseEvent[] = JSON.parse(fileContents);

    // Get today's date in YYYY-MM-DD format
    const today = new Date().toISOString().split('T')[0];

    // Filter to upcoming events only and transform
    const events: DisplayEvent[] = rawEvents
      .filter(event => event.date >= today)
      .map((event, index) => transformEvent(event, index))
      .sort((a, b) => a.date.localeCompare(b.date));

    return NextResponse.json({ events });
  } catch (error) {
    console.error('Error reading events:', error);
    return NextResponse.json(
      { error: 'Failed to load events' },
      { status: 500 }
    );
  }
}

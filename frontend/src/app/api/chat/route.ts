/**
 * API Route Handler for Chat Endpoint
 * Connects frontend to backend AG2 agent
 */

import { NextRequest, NextResponse } from 'next/server';
import { API_BASE } from '@/lib/config';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { message, max_turns = 5 } = body;

    if (!message || typeof message !== 'string') {
      return NextResponse.json(
        { error: 'Message is required and must be a string' },
        { status: 400 }
      );
    }

    // Forward request to backend
    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      cache: 'no-store',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        max_turns,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Backend request failed' }));
      return NextResponse.json(
        { error: error.error || 'Failed to communicate with backend' },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
    
  } catch (error) {
    console.error('Chat API error:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

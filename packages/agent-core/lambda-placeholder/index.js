// Placeholder Lambda handler for agent-core
// This will be replaced with actual implementation later

exports.handler = async (event) => {
  console.log('Event:', JSON.stringify(event, null, 2));

  // Health check endpoint
  if (event.rawPath === '/health' && event.requestContext.http.method === 'GET') {
    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        status: 'healthy',
        service: 'agent-core',
        timestamp: new Date().toISOString(),
      }),
    };
  }

  // Chat endpoint placeholder
  if (event.rawPath === '/agent/chat' && event.requestContext.http.method === 'POST') {
    const body = JSON.parse(event.body || '{}');
    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: 'Agent core placeholder - not yet implemented',
        receivedMessage: body.message || 'No message provided',
        timestamp: new Date().toISOString(),
      }),
    };
  }

  return {
    statusCode: 404,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ error: 'Not found', path: event.rawPath }),
  };
};

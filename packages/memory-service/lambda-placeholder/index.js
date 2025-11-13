// Placeholder Lambda handler for memory-service
exports.handler = async (event) => {
  const path = event.rawPath;
  const method = event.requestContext.http.method;

  if (path === '/memory/query' && method === 'POST') {
    const body = JSON.parse(event.body || '{}');
    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: 'Memory query placeholder',
        query: body.query || 'No query provided',
        memories: [],
      }),
    };
  }

  if (path === '/memory/store' && method === 'POST') {
    const body = JSON.parse(event.body || '{}');
    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: 'Memory store placeholder',
        stored: body.memory || 'No memory provided',
      }),
    };
  }

  return {
    statusCode: 404,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ error: 'Not found', path }),
  };
};

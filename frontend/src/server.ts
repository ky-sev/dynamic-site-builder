import {
  AngularNodeAppEngine,
  createNodeRequestHandler,
  isMainModule,
  writeResponseToNodeResponse,
} from '@angular/ssr/node';
import dotenv from 'dotenv';
import express, { type Request, type Response } from 'express';
import { join } from 'node:path';

dotenv.config({ path: join(process.cwd(), 'env.local') });

const browserDistFolder = join(import.meta.dirname, '../browser');
const workflowApiUrl = process.env['WORKFLOW_API_URL'] ?? 'http://127.0.0.1:8000';
const app = express();
const angularApp = new AngularNodeAppEngine();

app.use(express.json({ limit: '1mb' }));
app.use('/api', (_req, res, next) => {
  res.set('Cache-Control', 'no-store');
  next();
});

app.use('/api', async (req, res, next) => {
  try {
    const target = new URL(req.originalUrl, workflowApiUrl);
    const headers = new Headers();
    const contentType = req.get('content-type');
    const authorization = req.get('authorization');
    if (contentType) headers.set('content-type', contentType);
    if (authorization) headers.set('authorization', authorization);

    let body: string | undefined;
    if (req.method !== 'GET' && req.method !== 'HEAD' && req.body !== undefined) {
      body = JSON.stringify(req.body);
    }

    const upstream = await fetch(target, {
      method: req.method,
      headers,
      body,
      signal: AbortSignal.timeout(15_000),
    });
    const responseBody = await upstream.text();
    res.status(upstream.status);
    const upstreamContentType = upstream.headers.get('content-type');
    if (upstreamContentType) res.set('content-type', upstreamContentType);
    res.send(responseBody);
  } catch (error) {
    if (res.headersSent) {
      next(error);
      return;
    }
    console.error('Workflow API proxy request failed.', error);
    res.status(502).json({ error: 'Workflow API is unavailable.' });
  }
});

app.use(
  (
    error: unknown,
    req: Request,
    res: Response,
    next: (error?: unknown) => void,
  ): void => {
    if (req.path.startsWith('/api/')) {
      const isInvalidJson =
        typeof error === 'object' &&
        error !== null &&
        'type' in error &&
        error.type === 'entity.parse.failed';
      const isTooLarge =
        typeof error === 'object' &&
        error !== null &&
        'type' in error &&
        error.type === 'entity.too.large';
      const isInvalidPath = error instanceof URIError;
      const status = isTooLarge ? 413 : isInvalidJson || isInvalidPath ? 400 : 500;
      res.status(status).json({
        error: isTooLarge
          ? 'Request body exceeds the 1 MB limit.'
          : isInvalidJson
            ? 'Request body must contain valid JSON.'
            : isInvalidPath
              ? 'Request path is invalid.'
              : 'Request failed.',
      });
      if (status === 500) {
        console.error('Workflow API proxy failed.', error);
      }
      return;
    }
    next(error);
  },
);

app.use(
  express.static(browserDistFolder, {
    maxAge: '1y',
    index: false,
    redirect: false,
  }),
);

app.use((req, res, next) => {
  angularApp
    .handle(req)
    .then((response) =>
      response ? writeResponseToNodeResponse(response, res) : next(),
    )
    .catch(next);
});

if (isMainModule(import.meta.url) || process.env['pm_id']) {
  const port = process.env['PORT'] || 4000;
  app.listen(port, (error) => {
    if (error) {
      throw error;
    }
    console.log(`Node Express server listening on http://localhost:${port}`);
  });
}

export const reqHandler = createNodeRequestHandler(app);

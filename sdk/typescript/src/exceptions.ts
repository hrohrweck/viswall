export class ViswallAPIError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public responseBody?: unknown,
  ) {
    super(message);
    this.name = 'ViswallAPIError';
  }
}

export class AuthenticationError extends ViswallAPIError {
  constructor(message: string) {
    super(message, 401);
    this.name = 'AuthenticationError';
  }
}

export class NotFoundError extends ViswallAPIError {
  constructor(message: string) {
    super(message, 404);
    this.name = 'NotFoundError';
  }
}

export class ValidationError extends ViswallAPIError {
  constructor(
    message: string,
    public errors?: unknown,
  ) {
    super(message, 422);
    this.name = 'ValidationError';
  }
}

export class ServerError extends ViswallAPIError {
  constructor(message: string, statusCode: number) {
    super(message, statusCode);
    this.name = 'ServerError';
  }
}

export class RateLimitError extends ViswallAPIError {
  constructor(
    message: string,
    public retryAfter: number,
  ) {
    super(message, 429);
    this.name = 'RateLimitError';
  }
}

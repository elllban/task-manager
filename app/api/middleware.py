import hashlib

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.cache import cache


class IdempotencyMiddleware(BaseHTTPMiddleware):
    IDEMPOTENCY_TTL = 86400
    IDEMPOTENCY_HEADER = 'Idempotency-Key'

    async def dispatch(self, request: Request, call_next):
        if request.method not in ('POST', 'PUT', 'PATCH', 'DELETE'):
            return await call_next(request)

        idempotency_key = request.headers.get(self.IDEMPOTENCY_HEADER)
        if not idempotency_key:
            return await call_next(request)

        cache_key = f'idempotency:{idempotency_key}'

        cached = cache.get(cache_key)
        if cached is not None:
            return Response(
                content=cached['body'],
                status_code=cached['status_code'],
                media_type=cached['media_type'],
                headers=cached['headers'],
            )

        response = await call_next(request)

        if 200 <= response.status_code < 500:
            body = b''.join([chunk async for chunk in response.body_iterator])
            cache.set(
                cache_key,
                {
                    'body': body.decode() if isinstance(body, bytes) else body,
                    'status_code': response.status_code,
                    'media_type': response.media_type,
                    'headers': dict(response.headers),
                },
                self.IDEMPOTENCY_TTL,
            )
            response = Response(
                content=body,
                status_code=response.status_code,
                media_type=response.media_type,
                headers=dict(response.headers),
            )

        return response


def make_idempotency_key(user_id: int, path: str, timestamp_ns: int) -> str:
    raw = f'{user_id}:{path}:{timestamp_ns}'
    return hashlib.sha256(raw.encode()).hexdigest()[:32]

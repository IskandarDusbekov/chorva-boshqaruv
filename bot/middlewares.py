class AuditMiddleware:
    async def __call__(self, handler, event, data):
        return await handler(event, data)

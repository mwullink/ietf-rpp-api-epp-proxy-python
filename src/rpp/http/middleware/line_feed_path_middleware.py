from starlette.exceptions import HTTPException


class LineFeedPathMiddleware:
    """Answers a path with a line feed with a 404 Problem with 02001, as for an unknown path (detail `Not Found`).

    Connexion mounts the API on a pattern in which `.` does not match a line feed, so such a path is not routed
    but falls through to the Flask app, which fails with a 500 (#98). Raised here, inside Connexion's exception
    handling and before security, the 404 is rendered like every other error of the framework.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and "\n" in scope["path"]:
            raise HTTPException(status_code=404)
        await self.app(scope, receive, send)

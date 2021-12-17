import json
import uuid

import aiohttp
from aiohttp import web


routes = web.RouteTableDef()

def html_response(path):
    with open(path, 'r') as f:
        html = f.read()
    
    return web.Response(text=html, content_type='text/html')


async def broadcast(app, data):
    for ws in app['websockets'].values():
        await ws.send_bytes(data)


@routes.get('/')
async def handle_index(req):
    return html_response('./src/web/index.html')


@routes.post('/ffmpeg')
async def handle_ffmpeg(req):
    print("ffmpeg stream connected")
    while not req._payload.at_eof():
        end_chunk = False
        body = b''
        while not end_chunk:
            chunk, end_chunk = await req._payload.readchunk()
            body += chunk
        await broadcast(req.app, body)
    print("ffmpeg stream disconnected")


@routes.get('/video')
async def handle_video(req):
    ws_current = web.WebSocketResponse()
    ws_ready = ws_current.can_prepare(req)

    if not ws_ready.ok:
        return "Websocket not ready"
    
    await ws_current.prepare(req)

    name = str(uuid.uuid4())
    req.app['websockets'][name] = ws_current

    print("Client connected")

    while True:
        try:
            print(await ws_current.receive())
        except RuntimeError as e:
            print(e)
            break
    
    print("Client Disconnected")

    del req.app['websockets'][name]


@routes.get('/stats')
async def handle_stats(req):
    with open("stats.json", "r") as f:
        data = json.load(f)
    
    return web.json_response(data)


if __name__ == "__main__":
    app = web.Application()
    app.add_routes(routes)
    app.router.add_static('/static/', path='./src/web/static/', name='static')
    app['websockets'] = {}
    web.run_app(app, port=8080, host="0.0.0.0")

#!/usr/local/bin/python
import sys
import asyncio
from aiohttp import web
from charfinder import UnicodeNameIndex

TEMPLATE_NAME = "http-charfinder.html"
SAMPLE_WORDS = (
    "bismillah chess cat circled Malayalam digit"
    " Roman face Ethiopic black mark symbol dot"
    " operator Braille hexagram"
).split()

ROW_TPL = "<tr><td>{code_str}</td><th>{char}</th><td>{name}</td></tr>"
LINK_TPL = '<a href="/?query={0}" title="find &quot;{0}&quot;">{0}</a>'
LINKS_HTML = ", ".join(
    LINK_TPL.format(word) for word in sorted(SAMPLE_WORDS, key=str.upper)
)

index = UnicodeNameIndex()
with open(TEMPLATE_NAME) as tpl:
    template = tpl.read()
template = template.replace("{links}", LINKS_HTML)


def home(request):
    query = request.query.get("query", "")
    print(f"query: {query!r}")
    if query:
        descriptions = list(index.find_descriptions(query))
        res = "\n".join(
            ROW_TPL.format(**descr._asdict()) for descr in descriptions
        )
        msg = index.status(query, len(descriptions))
    else:
        descriptions = []
        res = ""
        msg = "enter words describing characters"

    html = template.format(query=query, result=res, message=msg)
    print("sending {} results".format(len(descriptions)))
    return web.Response(content_type="text/html", charset="utf-8", text=html)


def init(addr, port):
    app = web.Application()
    app.router.add_get("/", home)
    return app


def main(addr="127.0.0.1", port=8888):
    port = int(port)
    app = init(addr, port)
    runner = web.AppRunner(app)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, addr, port)
    loop.run_until_complete(site.start())
    print("serving on {}:{}. hit ctrl-c to stop".format(addr, port))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.run_until_complete(runner.cleanup())

    loop.close()
    print("server shutting down")


if __name__ == "__main__":
    main(*sys.argv[1:])
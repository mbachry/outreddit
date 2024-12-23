import html
from urllib.parse import urlparse

import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

app = FastAPI()

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def get_title(data):
    main = next(
        d['data']['children'][0]
        for d in data
        if len(d['data']['children']) == 1 and d['data']['children'][0]['kind'] == 't3'
    )
    return main['data']['title']


def get_comment(data):
    comment = next(
        (
            d['data']['children'][0]
            for d in data
            if len(d['data']['children']) == 1 and d['data']['children'][0]['kind'] == 't1'
        ),
        None,
    )
    if comment is None:
        raise HTTPException(status_code=400, detail='single comment link required')
    return comment['data']


def get_replies(comment):
    if not comment['replies']:
        return []
    return [r['data'] for r in comment['replies']['data']['children']]


def get_full_comment(comment):
    body = html.unescape(comment['body_html'])
    next_comments = [c for c in get_replies(comment) if c['author'] == comment['author']]
    for next_comment in next_comments:
        body += get_full_comment(next_comment)
    return body


@app.get('/r', response_class=HTMLResponse)
@limiter.limit('3/minute')
def root(request: Request, url: str):
    url = url.rstrip('/')

    parts = urlparse(url)
    if parts.scheme != 'https':
        raise HTTPException(status_code=400, detail=f'invalid scheme: {parts.scheme}')
    if parts.netloc not in ('www.reddit.com', 'reddit.com'):
        raise HTTPException(status_code=400, detail=f'invalid netloc: {parts.netloc}')

    json_url = f'https://{parts.netloc}{parts.path}.json'
    response = requests.get(json_url, headers={'User-agent': 'Firefox'}, timeout=15)
    response.raise_for_status()
    data = [d for d in response.json() if d['kind'] == 'Listing']

    title = get_title(data)
    comment = get_comment(data)
    body = f'<!DOCTYPE html><head><title>{title}</title></head>\n'
    body += f'<article><header><h1>{title}</h1></header>\n'
    body += get_full_comment(comment)
    body += '</article>\n'
    return body

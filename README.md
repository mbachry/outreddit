outreddit
=========

Are you an avid fan of /r/AskHistorians subreddit? Do you use pocket
service? Do you read pocket articles on a Kobo reader? Do you have a
server/vps? This tiny HTTP server will convert reddit threads to a
format pocket can parse and save to your Kobo.

Install
=======

Install `uv` and git-clone/copy the project dir to your server. Pick
and local port and run with:

```
uv run uvicorn --port 7777 outreddit:app
```

Add a systemd unit to make the service permanent:

```
[Unit]
Description=outreddit

[Service]
orkingDirectory=/path/to/outreddit
ExecStart=/bin/uv run uvicorn --port 7777 outreddit:app
DynamicUser=yes
PrivateDevices=yes
SystemCallFilter=@system-service
RestrictAddressFamilies=AF_INET
MemoryDenyWriteExecute=yes

[Install]
WantedBy=multi-user.target
```

Add an nginx redirect:

```
location /outreddit {
    proxy_pass http://127.0.0.1:7777;
    proxy_set_header Host $host;
}
```

Usage
=====

Grab a single-comment link to a comment and pass it as `url` parameter, eg.:

```
https://example.com/outreddit?url=https://www.reddit.com/r/AskHistorians/comments/14x8cs/what_did_it_cost_to_go_see_an_actual_mozart_opera/c7hdzih/
```

Save the page to pocket.

Notes
=====

Since pocket doesn't support authentication your service is exposed to
the entire internet. In order to prevent your server from becoming an
"open relay" reddit proxy, there's a fixed 3req/minute rate
limit. It's also best to keep `location` in nginx conf secret:
consider prefixing with a random uuid, etc.

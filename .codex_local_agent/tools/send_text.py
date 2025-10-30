#!/usr/bin/env python3
import argparse, http.client
ap = argparse.ArgumentParser()
ap.add_argument("--port", type=int, default=37915)
ap.add_argument("text", nargs="+")
a = ap.parse_args()
conn = http.client.HTTPConnection("127.0.0.1", a.port, timeout=3.0)
conn.request("POST", "/send", " ".join(a.text).encode("utf-8"), headers={"Content-Type":"text/plain"})
resp = conn.getresponse()
print(resp.status, resp.reason)

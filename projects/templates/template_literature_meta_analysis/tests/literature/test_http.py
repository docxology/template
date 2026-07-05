from __future__ import annotations
import requests
from werkzeug.wrappers import Response
from literature.http import request_with_retry

def test_request_with_retry_recovers_from_503(httpserver)->None:
    calls={"n":0}
    def handler(_request):
        calls["n"]+=1
        return Response("err",status=503) if calls["n"]==1 else Response("{}",status=200)
    httpserver.expect_request("/ping").respond_with_handler(handler)
    resp=request_with_retry(requests.Session(),"GET",httpserver.url_for("/ping"),delay_override=lambda _s:None,max_retries=2)
    assert resp.status_code==200 and calls["n"]==2

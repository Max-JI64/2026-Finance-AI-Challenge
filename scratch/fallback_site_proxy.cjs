// Local-only fault injection; all ordinary pages/assets/catalogs use real V5.
const http = require("node:http");
for (const [port, tier] of [[8767, 2], [8768, 3]]) {
  http.createServer((req, res) => {
    const route = new URL(req.url, "http://localhost").pathname;
    if (route === "/api/v5/orchestrate" ||
        (tier === 3 && route === "/static/fallback-example.json")) {
      req.resume();
      res.writeHead(503, {"Content-Type":"application/json; charset=utf-8","Cache-Control":"no-store"});
      res.end(JSON.stringify({message:"로컬 fallback 시험: 의도적으로 발생시킨 오류"}));
      return;
    }
    const upstream = http.request({
      hostname:"127.0.0.1", port:8003, path:req.url, method:req.method,
      headers:{...req.headers,host:"127.0.0.1:8003"},
    }, reply => {
      res.writeHead(reply.statusCode, reply.headers);
      reply.pipe(res);
    });
    upstream.on("error", () => {
      if (!res.headersSent) res.writeHead(502, {"Content-Type":"text/plain; charset=utf-8"});
      res.end("로컬 V5 서버를 준비 중입니다. 잠시 후 새로고침해 주세요.");
    });
    req.pipe(upstream);
  }).listen(port, "127.0.0.1", () => console.log("Real V5 fault injection tier " + tier + ": " + port));
}

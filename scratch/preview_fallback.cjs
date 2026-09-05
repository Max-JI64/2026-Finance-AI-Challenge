const http = require("node:http");
const fs = require("node:fs");
const path = require("node:path");
const root = path.resolve(__dirname, "../v5/static");
for (const [port, tier] of [[8765, 2], [8766, 3]]) {
  http.createServer((req, res) => {
    res.setHeader("Cache-Control", "no-store");
    if (req.url === "/static/demo-fallback.js") {
      res.setHeader("Content-Type", "text/javascript; charset=utf-8");
      return res.end(fs.readFileSync(path.join(root, "demo-fallback.js")));
    }
    if (req.url === "/static/fallback-example.json") {
      res.setHeader("Content-Type", "application/json; charset=utf-8");
      res.statusCode = tier === 3 ? 503 : 200;
      return res.end(tier === 3 ? '{"error":"intentional preview failure"}' : fs.readFileSync(path.join(root, "fallback-example.json")));
    }
    res.setHeader("Content-Type", "text/html; charset=utf-8");
    res.end('<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+tier+'차 fallback 로컬 확인</title><body><h1>'+tier+'차 fallback 로컬 확인</h1><p>실제 배포용 fallback 파일을 실행합니다. 3차 화면은 저장 예시 요청에 503 오류를 발생시킵니다.</p><a href="http://127.0.0.1:8765">2차 확인</a> · <a href="http://127.0.0.1:8766">3차 확인</a><script src="/static/demo-fallback.js"></script><script>window.openDemoFallback();</script></body></html>');
  }).listen(port, "127.0.0.1", () => console.log("Fallback preview " + tier + ": http://127.0.0.1:" + port));
}

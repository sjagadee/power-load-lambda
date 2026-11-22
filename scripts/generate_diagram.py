import json, random, sys, html, base64, pathlib

random.seed(7)
OUT = sys.argv[1]
els = []
svg = []

C = {
    "blue": ("#1971c2", "#d0ebff"), "purple": ("#6741d9", "#e5dbff"),
    "orange": ("#e8590c", "#ffe8cc"), "teal": ("#0c8599", "#c5f6fa"),
    "red": ("#c92a2a", "#fff5f5"), "pink": ("#c2255c", "#ffdeeb"),
    "green": ("#2b8a3e", "#ebfbee"), "gray": ("#495057", "#f8f9fa"),
    "yellow": ("#e67700", "#fff9db"),
}
FONT = {2: "Helvetica, Arial, sans-serif", 3: "Menlo, Consolas, monospace", 5: "Virgil, 'Comic Sans MS', cursive"}
_id = [0]
FILES = {}
ICON_DIR = pathlib.Path(OUT) / "icons"


def icon_data(name):
    return "data:image/png;base64," + base64.b64encode((ICON_DIR / f"{name}.png").read_bytes()).decode()


def image(x, y, size, name, group):
    fid = f"icon-{name}"
    FILES[fid] = {"mimeType": "image/png", "id": fid, "dataURL": icon_data(name), "created": 1}
    e = base("image", x, y, size, size, "transparent", "transparent", roundness=None, sw=1)
    e.update(fileId=fid, status="saved", scale=[1, 1], groupIds=[group])
    svg.append(f'<image x="{x}" y="{y}" width="{size}" height="{size}" href="{icon_data(name)}"/>')
    return e


def nid(p):
    _id[0] += 1
    return f"{p}{_id[0]}"


def base(t, x, y, w, h, stroke, bg, **kw):
    e = dict(id=nid(t[:2]), type=t, x=x, y=y, width=w, height=h, angle=0,
             strokeColor=stroke, backgroundColor=bg, fillStyle="solid",
             strokeWidth=kw.get("sw", 2), strokeStyle=kw.get("ss", "solid"),
             roughness=kw.get("rough", 1), opacity=100, groupIds=[], frameId=None,
             roundness=kw.get("roundness", {"type": 3}), seed=random.randint(1, 2**31),
             version=1, versionNonce=random.randint(1, 2**31), isDeleted=False,
             boundElements=[], updated=1, link=None, locked=False)
    els.append(e)
    return e


def text_el(x, y, w, h, s, size, color, family=2, align="center", valign="middle", container=None):
    e = base("text", x, y, w, h, color, "transparent", roundness=None)
    e.update(text=s, originalText=s, fontSize=size, fontFamily=family, textAlign=align,
             verticalAlign=valign, containerId=container, lineHeight=1.25, autoResize=True)
    return e


def svg_text(cx, y_top, s, size, color, family=2, anchor="middle", weight_first=False):
    lines = s.split("\n")
    out = []
    for i, ln in enumerate(lines):
        wt = ' font-weight="700"' if (weight_first and i == 0) else ""
        out.append(f'<text x="{cx}" y="{y_top + size + i*size*1.25:.1f}" font-family="{FONT[family]}" '
                   f'font-size="{size}" fill="{color}" text-anchor="{anchor}"{wt} xml:space="preserve">{html.escape(ln)}</text>')
    svg.append("\n".join(out))


def box(x, y, w, h, label, color, size=16, family=2, ss="solid", align="center", bold=True, icon=None, icon_size=56):
    stroke, bg = C[color]
    r = base("rectangle", x, y, w, h, stroke, bg, ss=ss)
    n = label.count("\n") + 1
    th = n * size * 1.25
    dash = ' stroke-dasharray="8 6"' if ss == "dashed" else ""
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{bg}" stroke="{stroke}" stroke-width="2"{dash}/>')
    if icon:
        g = nid("grp")
        r["groupIds"] = [g]
        pad = 14
        image(x + (w - icon_size) / 2, y + pad, icon_size, icon, g)
        ty = y + pad + icon_size + 10 + (h - pad - icon_size - 10 - th - 10) / 2
        t = text_el(x + 8, ty, w - 16, th, label, size, "#1e1e1e", family, "center", "top")
        t["groupIds"] = [g]
        svg_text(x + w / 2, ty - 3, label, size, "#1e1e1e", family, weight_first=bold)
        return r
    t = text_el(x + 8, y + (h - th) / 2, w - 16, th, label, size, "#1e1e1e", family, align, container=r["id"])
    r["boundElements"].append({"type": "text", "id": t["id"]})
    if align == "center":
        svg_text(x + w / 2, y + (h - th) / 2 - 3, label, size, "#1e1e1e", family, weight_first=bold)
    else:
        svg_text(x + 16, y + (h - th) / 2 - 3, label, size, "#1e1e1e", family, anchor="start", weight_first=bold)
    return r


def zone(x, y, w, h, title, color):
    stroke, bg = C[color]
    base("rectangle", x, y, w, h, stroke, bg, ss="dashed", sw=1, rough=0)
    els[-1]["opacity"] = 60
    text_el(x + 16, y + 10, len(title) * 11, 25, title, 20, stroke, 5, "left", "top")
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="{bg}" fill-opacity="0.6" stroke="{stroke}" stroke-dasharray="6 6"/>')
    svg_text(x + 16, y + 8, title, 20, stroke, 5, anchor="start")


def arrow(pts, label=None, color="#343a40", start=None, end=None, lpos=None, ss="solid"):
    x0, y0 = pts[0]
    rel = [[px - x0, py - y0] for px, py in pts]
    xs = [p[0] for p in rel]; ys = [p[1] for p in rel]
    a = base("arrow", x0, y0, max(xs) - min(xs), max(ys) - min(ys), color, "transparent",
             roundness={"type": 2} if len(pts) == 2 else None, ss=ss)
    a.update(points=rel, lastCommittedPoint=None, startArrowhead=None, endArrowhead="arrow",
             startBinding={"elementId": start["id"], "focus": 0, "gap": 6} if start else None,
             endBinding={"elementId": end["id"], "focus": 0, "gap": 6} if end else None,
             elbowed=False)
    for b in (start, end):
        if b:
            b["boundElements"].append({"type": "arrow", "id": a["id"]})
    dash = ' stroke-dasharray="7 5"' if ss == "dashed" else ""
    svg.append(f'<polyline points="{" ".join(f"{p[0]},{p[1]}" for p in pts)}" fill="none" stroke="{color}" '
               f'stroke-width="2"{dash} marker-end="url(#ah)"/>')
    if label:
        size = 13
        n = label.count("\n") + 1
        w = max(len(l) for l in label.split("\n")) * size * 0.56 + 12
        h = n * size * 1.25 + 6
        cx, cy = lpos
        t = text_el(cx - w / 2, cy - h / 2, w, h, label, size, "#343a40", 2, container=a["id"])
        a["boundElements"].append({"type": "text", "id": t["id"]})
        svg.append(f'<rect x="{cx-w/2:.1f}" y="{cy-h/2:.1f}" width="{w:.1f}" height="{h:.1f}" rx="4" fill="#ffffff"/>')
        svg_text(cx, cy - h / 2 + 1, label, size, "#343a40")
    return a


W, H = 1420, 1040
# Title
text_el(30, 18, 1000, 35, "Serverless CRUD Microservice — Power Tuning & Load Testing", 28, "#1e1e1e", 5, "left", "top")
svg_text(30, 14, "Serverless CRUD Microservice — Power Tuning & Load Testing", 28, "#1e1e1e", 5, anchor="start")
text_el(30, 56, 900, 20, "API Gateway → Lambda → DynamoDB, right-sized with AWS Lambda Power Tuning and Postman performance runs", 15, "#868e96", 2, "left", "top")
svg_text(30, 54, "API Gateway → Lambda → DynamoDB, right-sized with AWS Lambda Power Tuning and Postman performance runs", 15, "#868e96", 2, anchor="start")

# Zone 1: request path
zone(20, 90, 1380, 480, "① Request path", "gray")
client = box(50, 150, 230, 180, "Client\nPostman / curl\nHTTPS POST (JSON)", "teal", icon="postman")
apigw = box(355, 150, 250, 180, "Amazon API Gateway\nREST · DynamoDBOperations\nPOST /DynamoDBManager\nstage: prod", "purple", 15, icon="api-gateway")
lam = box(690, 150, 260, 180, "AWS Lambda\nLambdaFunctionOverHttps\nPython · boto3 · 512 MB\noperation router", "orange", 15, icon="lambda")
ddb = box(1060, 150, 300, 180, "Amazon DynamoDB\ntable: lambda-apigateway\npartition key: id (String)", "blue", 15, icon="dynamodb")
iam = box(675, 395, 290, 155, "IAM role · lambda-apigateway-role\n+ DynamoDB CRUD policy\n+ CloudWatch Logs policy", "red", 14, ss="dashed", icon="iam", icon_size=50)
cw = box(1060, 395, 300, 155, "Amazon CloudWatch Logs\n/aws/lambda/LambdaFunctionOverHttps", "pink", 14, icon="cloudwatch", icon_size=50)

arrow([(286, 240), (349, 240)], start=client, end=apigw)
svg_text(317, 112, "{ operation,\n  tableName,\n  payload }", 12, "#343a40", 3)
text_el(270, 107, 100, 45, "{ operation,\n  tableName,\n  payload }", 12, "#343a40", 3)
arrow([(611, 240), (684, 240)], "invoke", start=apigw, end=lam, lpos=(647, 222))
arrow([(956, 240), (1054, 240)], "put · get · update\ndelete · scan", start=lam, end=ddb, lpos=(1005, 272))
arrow([(820, 389), (820, 336)], "assumes", start=iam, end=lam, lpos=(866, 362), ss="dashed")
arrow([(956, 310), (1054, 440)], "logs", start=lam, end=cw, lpos=(1003, 375))

# Zone 2: optimisation
zone(20, 590, 1380, 430, "② Performance optimisation", "yellow")
pm = box(50, 640, 300, 175, "Postman Performance Runner\nRamp up (30 s) · 10 VUs · 2 min\nrequest: POST list", "teal", 14, icon="postman", icon_size=50)
sf = box(50, 835, 300, 170, "AWS Step Functions\nLambda Power Tuning (SAR app)\n128 · 256 · 512 · 1024 MB · num 10", "green", 14, icon="step-functions", icon_size=50)

arrow([(356, 728), (480, 728), (480, 336)], "load test\nvia API", start=pm, end=apigw, lpos=(480, 470))
arrow([(356, 920), (630, 920), (630, 300), (684, 300)], "invoke at each\nmemory size", start=sf, end=lam, lpos=(630, 680))

tune = ("Lambda Power Tuning results  (num = 10)\n"
        "Memory    Avg duration    Cost / invoke\n"
        "128 MB      472.6 ms      $0.00000099\n"
        "256 MB      670.5 ms      $0.00000282\n"
        "512 MB       85.3 ms      $0.00000072   ← cheapest · chosen\n"
        "1024 MB      48.4 ms      $0.00000082   ← fastest")
box(700, 640, 670, 175, tune, "gray", 15, 3, align="left")
load = ("Postman load test  (10 VUs · ramp-up · 2 min · 0 % errors)\n"
        "Memory    Avg     P95     P99     Req/s   Requests\n"
        "128 MB    350ms   421ms   796ms   20.5    2,481\n"
        "512 MB    144ms   167ms   251ms   48.7    5,864\n"
        "→ 512 MB (balanced): 59 % lower avg latency · 2.4× throughput")
box(700, 835, 670, 170, load, "gray", 15, 3, align="left")

doc = {"type": "excalidraw", "version": 2, "source": "https://excalidraw.com", "elements": els,
       "appState": {"gridSize": None, "viewBackgroundColor": "#ffffff"}, "files": FILES}
open(f"{OUT}/architecture.excalidraw", "w").write(json.dumps(doc, indent=2))

svg_doc = (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {H}" width="{W}" height="{H}">\n'
           '<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
           '<path d="M0,0 L10,5 L0,10 z" fill="#343a40"/></marker></defs>\n'
           f'<rect width="{W}" height="{H}" fill="#ffffff"/>\n' + "\n".join(svg) + "\n</svg>\n")
open(f"{OUT}/architecture.svg", "w").write(svg_doc)
print(len(els), "elements")

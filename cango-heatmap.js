(function () {
  window.runHeatmap = runHeatmap;
  function runHeatmap() {
  const root = document.getElementById("cango-heatmap-root");
  if (!root) { console.error("[Heatmap] 找不到 #cango-heatmap-root"); return; }

  const TOPICS = [
    "气候与生态环境","社区发展与减贫","教育与能力建设","可持续发展目标",
    "人权与法治治理","性别平等与妇女赋权","健康与公共卫生","食品安全与农业",
    "人道援助与灾害风险","公民社会与全球治理","数字技术与创新","国际合作与青年发展",
  ];
  const SHORT = [
    "气候生态","社区减贫","教育建设","SDG目标",
    "人权法治","性别平等","公共卫生","食品农业",
    "人道援助","公民治理","数字技术","国际合作",
  ];
  const MATRIX = [
    [75,18, 9,30,14, 8, 4,10, 2,14, 8, 5],
    [18,77,26,13,13,18,14, 8,16, 9, 1, 9],
    [ 9,26,71,23,13, 8,12, 1, 2,19, 4,19],
    [30,13,23,68,16, 4, 3, 4, 1,15, 8,14],
    [14,13,13,16,53, 6, 3, 2, 5,15, 1, 5],
    [ 8,18, 8, 4, 6,35, 5, 0, 7, 4, 0, 6],
    [ 4,14,12, 3, 3, 5,25, 1, 6, 0, 0, 1],
    [10, 8, 1, 4, 2, 0, 1,15, 2, 0, 0, 0],
    [ 2,16, 2, 1, 5, 7, 6, 2,24, 1, 0, 6],
    [14, 9,19,15,15, 4, 0, 0, 1,52, 3,11],
    [ 8, 1, 4, 8, 1, 0, 0, 0, 0, 3,14, 0],
    [ 5, 9,19,14, 5, 6, 1, 0, 6,11, 0,41],
  ];
  const MECE_NOTE = {
    "气候与生态环境":     "合并27个标签：环境与气候变化、气候变化、气候行动、生物多样性保护、能源转型、绿色金融等",
    "社区发展与减贫":     "合并13个标签：社区发展与减贫、社区发展、减贫、农村发展、生计支持、地方治理等",
    "教育与能力建设":     "合并12个标签：教育与能力建设、能力建设、教育与科研、技能培训、组织发展等",
    "可持续发展目标":     "保留独立：可持续发展目标推进（SDG跨领域框架，单独成类）",
    "人权与法治治理":     "合并19个标签：人权与社会正义、法治与民主治理、民主治理、政策倡导、和平建设等",
    "性别平等与妇女赋权": "合并13个标签：性别平等与多样性、性别平等、女性赋权、妇女权利、社会包容等",
    "健康与公共卫生":     "合并3个标签：健康与公共卫生、健康与WASH、人口健康",
    "食品安全与农业":     "合并3个标签：食品安全与可持续农业、粮食安全、食品安全与生计恢复",
    "人道援助与灾害风险": "合并3个标签：灾害风险与人道援助、人道援助与灾害风险、人道事务",
    "公民社会与全球治理": "合并16个标签：公民社会参与与全球治理、全球治理、公益生态系统建设、企业社会责任等",
    "数字技术与创新":     "合并4个标签：数字技术与治理创新、数字与人工智能、科技研发、社会创新",
    "国际合作与青年发展": "合并27个标签：发展合作与援助有效性、国际交流与合作、青年发展系列、经济发展系列等",
  };

  function offColor(v, max) {
    if (v === 0) return "#0B1525";
    var t = Math.pow(v / max, 0.7);
    return "rgb("+Math.round(5+t*20)+","+Math.round(60+t*152)+","+Math.round(90+t*122)+")";
  }
  function diagColor(v, max) {
    if (v === 0) return "#0B1525";
    var t = Math.pow(v / max, 0.7);
    return "rgb("+Math.round(90+t*80)+","+Math.round(50+t*40)+","+Math.round(180+t*55)+")";
  }

  var N = TOPICS.length;
  var maxOff = 0, maxDiag = 0;
  for (var i = 0; i < N; i++) {
    for (var j = 0; j < N; j++) {
      if (i === j) { if (MATRIX[i][j] > maxDiag) maxDiag = MATRIX[i][j]; }
      else          { if (MATRIX[i][j] > maxOff)  maxOff  = MATRIX[i][j]; }
    }
  }

  var hoverR = -1, hoverC = -1, pinR = -1, pinC = -1, showMece = false;

  root.innerHTML = "";
  root.setAttribute("style", "width:100%;max-width:100%;display:block;font-family:'Noto Sans SC','PingFang SC','Microsoft YaHei',sans-serif;background:#080F1E;border-radius:16px;padding:28px 20px 36px;box-sizing:border-box;color:#F1F5F9;user-select:none;border:1px solid #1E293B;");

  var headerDiv = document.createElement("div");
  headerDiv.style.marginBottom = "18px";
  headerDiv.innerHTML =
    '<div style="font-size:11px;color:#38BDF8;letter-spacing:4px;text-transform:uppercase;margin-bottom:5px;">CANGO · 议题共现分析（MECE清洗版）</div>' +
    '<h2 style="margin:0;font-size:20px;font-weight:900;background:linear-gradient(135deg,#38BDF8,#2DD4BF,#A78BFA);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">哪些机构同时关注多个议题？</h2>' +
    '<p style="margin:8px 0 10px;font-size:12px;color:#64748B;max-width:600px;line-height:1.7;">原始 <b style="color:#94A3B8">157</b> 个议题标签经 MECE 原则合并为 <b style="color:#38BDF8">12 个互斥类别</b>。格子数字 = 同时关注两个议题的机构数，<span style="color:#A78BFA">紫色对角线</span> = 该类别总机构数。悬停查看详情，点击固定。</p>';
  var meceBtn = document.createElement("button");
  meceBtn.textContent = "▸ 展开 MECE 清洗说明";
  meceBtn.setAttribute("style", "background:rgba(255,255,255,0.04);border:1px solid #1E293B;border-radius:8px;padding:5px 14px;color:#64748B;font-size:12px;cursor:pointer;font-family:inherit;transition:all 0.2s;");
  headerDiv.appendChild(meceBtn);
  root.appendChild(headerDiv);

  var meceBox = document.createElement("div");
  meceBox.setAttribute("style", "display:none;margin-bottom:18px;background:rgba(255,255,255,0.02);border:1px solid #1E293B;border-radius:12px;padding:16px 20px;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:10px;");
  TOPICS.forEach(function(t) {
    var item = document.createElement("div");
    item.setAttribute("style", "display:flex;gap:8px;align-items:flex-start;");
    item.innerHTML = '<div style="width:6px;height:6px;border-radius:2px;background:#38BDF8;margin-top:4px;flex-shrink:0;"></div><div><div style="font-size:12px;font-weight:700;color:#CBD5E1;">'+t+'</div><div style="font-size:10px;color:#475569;line-height:1.5;">'+MECE_NOTE[t]+'</div></div>';
    meceBox.appendChild(item);
  });
  root.appendChild(meceBox);

  meceBtn.addEventListener("click", function() {
    showMece = !showMece;
    meceBox.style.display = showMece ? "grid" : "none";
    meceBtn.textContent = showMece ? "▾ 收起 MECE 清洗说明" : "▸ 展开 MECE 清洗说明";
    meceBtn.style.color = showMece ? "#38BDF8" : "#64748B";
    meceBtn.style.background = showMece ? "rgba(56,189,248,0.15)" : "rgba(255,255,255,0.04)";
    meceBtn.style.borderColor = showMece ? "#38BDF8" : "#1E293B";
  });

  var contentWrap = document.createElement("div");
  contentWrap.setAttribute("style", "width:100%;max-width:920px;margin:0 auto;");
  root.appendChild(contentWrap);

  var mainRow = document.createElement("div");
  mainRow.setAttribute("style", "display:flex;gap:20px;align-items:flex-start;flex-wrap:wrap;");
  contentWrap.appendChild(mainRow);

  var mapWrap = document.createElement("div");
  mapWrap.setAttribute("style", "overflow-x:auto;flex:1;min-width:0;");
  mainRow.appendChild(mapWrap);

  var CELL = 42, LABEL_W = 98;

  var colHead = document.createElement("div");
  colHead.setAttribute("style", "display:flex;margin-left:"+LABEL_W+"px;");
  SHORT.forEach(function(s) {
    var d = document.createElement("div");
    d.className = "hm-col-label";
    d.textContent = s;
    d.setAttribute("style", "width:"+CELL+"px;font-size:9px;color:#475569;text-align:center;transform:rotate(-38deg) translateX(5px);transform-origin:bottom left;height:65px;display:flex;align-items:flex-end;line-height:1.25;padding-bottom:2px;transition:color 0.15s;");
    colHead.appendChild(d);
  });
  mapWrap.appendChild(colHead);

  var cellEls = [];
  for (var ri = 0; ri < N; ri++) {
    (function(i) {
      var rowDiv = document.createElement("div");
      rowDiv.setAttribute("style", "display:flex;align-items:center;margin-bottom:2px;");
      var lbl = document.createElement("div");
      lbl.className = "hm-row-label";
      lbl.setAttribute("data-row", i);
      lbl.textContent = SHORT[i];
      lbl.setAttribute("style", "width:"+(LABEL_W-8)+"px;font-size:11px;text-align:right;padding-right:8px;color:#64748B;white-space:nowrap;flex-shrink:0;transition:color 0.15s;");
      rowDiv.appendChild(lbl);
      cellEls[i] = [];
      for (var ci = 0; ci < N; ci++) {
        (function(j) {
          var val = MATRIX[i][j];
          var isDiag = (i === j);
          var bg = isDiag ? diagColor(val, maxDiag) : offColor(val, maxOff);
          var txThreshold = isDiag ? maxDiag * 0.38 : maxOff * 0.38;
          var txCol = val > txThreshold ? "rgba(255,255,255,0.92)" : "rgba(255,255,255,0.38)";
          var cell = document.createElement("div");
          cell.textContent = val > 0 ? val : "·";
          cell.setAttribute("style",
            "width:"+(CELL-2)+"px;height:"+(CELL-2)+"px;margin:1px;" +
            "background:"+bg+";border:1px solid transparent;border-radius:5px;" +
            "display:flex;align-items:center;justify-content:center;" +
            "font-size:"+(val > 9 ? 12 : 11)+"px;font-weight:700;color:"+txCol+";" +
            "cursor:pointer;transition:transform 0.1s,border 0.1s,opacity 0.12s;position:relative;z-index:1;");
          cell.addEventListener("mouseenter", function() { hoverR = i; hoverC = j; updateHL(); });
          cell.addEventListener("mouseleave", function() { hoverR = -1; hoverC = -1; updateHL(); });
          cell.addEventListener("click", function() {
            if (pinR === i && pinC === j) { pinR = -1; pinC = -1; } else { pinR = i; pinC = j; }
            updateHL();
          });
          rowDiv.appendChild(cell);
          cellEls[i][j] = cell;
        })(ci);
      }
      mapWrap.appendChild(rowDiv);
    })(ri);
  }

  var legendDiv = document.createElement("div");
  legendDiv.setAttribute("style", "display:flex;gap:18px;margin-top:12px;margin-left:"+LABEL_W+"px;flex-wrap:wrap;align-items:center;");
  legendDiv.innerHTML =
    '<div style="display:flex;align-items:center;gap:6px;"><div style="width:10px;height:10px;border-radius:2px;background:#9060C8;"></div><span style="font-size:10px;color:#475569;">对角线 = 该议题机构总数</span></div>' +
    '<div style="display:flex;align-items:center;gap:2px;">' +
    [0,0.2,0.45,0.7,1].map(function(t,k){ return '<div style="width:20px;height:10px;border-radius:'+(k===0?"2px 0 0 2px":k===4?"0 2px 2px 0":"0")+';background:'+offColor(Math.round(t*maxOff),maxOff)+';"></div>'; }).join("") +
    '<span style="font-size:10px;color:#475569;margin-left:5px;">共现 0 → '+maxOff+' 家</span></div>';
  mapWrap.appendChild(legendDiv);

  var panel = document.createElement("div");
  panel.setAttribute("style", "flex:0 0 240px;");
  mainRow.appendChild(panel);

  var detailCard = document.createElement("div");
  detailCard.setAttribute("style", "background:rgba(255,255,255,0.02);border:1px solid #1E293B;border-radius:12px;padding:16px 18px;min-height:128px;margin-bottom:14px;transition:all 0.2s;");
  detailCard.innerHTML = '<div style="color:#334155;font-size:12px;line-height:1.8;">悬停格子查看共现详情<br>点击可固定显示<div style="margin-top:10px;font-size:10px;color:#1E3A5A;line-height:1.6;">数据来源：CANGO 海外资源库<br>2026年3月 · 202 家机构<br>MECE 清洗：157 → 12 类</div></div>';
  panel.appendChild(detailCard);

  var pairs = [];
  for (var pi = 0; pi < N; pi++) for (var pj = pi+1; pj < N; pj++) if (MATRIX[pi][pj] > 0) pairs.push([pi, pj, MATRIX[pi][pj]]);
  pairs.sort(function(a,b){ return b[2]-a[2]; });

  var pairList = document.createElement("div");
  pairList.setAttribute("style", "background:rgba(255,255,255,0.02);border:1px solid #1E293B;border-radius:12px;padding:14px 16px;");
  var pairHeader = document.createElement("div");
  pairHeader.setAttribute("style", "font-size:10px;color:#475569;letter-spacing:2px;text-transform:uppercase;margin-bottom:10px;");
  pairHeader.textContent = "共现 Top 10";
  pairList.appendChild(pairHeader);

  var pairEls = [];
  pairs.slice(0, 10).forEach(function(pair) {
    var a = pair[0], b = pair[1], cnt = pair[2];
    var d = document.createElement("div");
    d.setAttribute("style", "display:flex;align-items:center;gap:8px;padding:5px 8px;border-radius:6px;margin-bottom:2px;cursor:pointer;transition:background 0.15s;");
    d.innerHTML = '<span style="font-size:14px;font-weight:900;color:#38BDF8;min-width:22px;text-align:right;">'+cnt+'</span><div style="flex:1;font-size:10px;color:#94A3B8;line-height:1.4;">'+SHORT[a]+' <span style="color:#334155">×</span> '+SHORT[b]+'</div><div style="height:3px;border-radius:2px;background:#38BDF8;opacity:0.4;width:'+Math.round((cnt/30)*44)+'px;flex-shrink:0;"></div>';
    d.addEventListener("mouseenter", function() { hoverR = a; hoverC = b; updateHL(); });
    d.addEventListener("mouseleave", function() { hoverR = -1; hoverC = -1; updateHL(); });
    d.addEventListener("click", function() {
      if (pinR === a && pinC === b) { pinR = -1; pinC = -1; } else { pinR = a; pinC = b; }
      updateHL();
    });
    pairList.appendChild(d);
    pairEls.push({ el: d, a: a, b: b });
  });
  panel.appendChild(pairList);

  function updateHL() {
    var aR = pinR >= 0 ? pinR : hoverR;
    var aC = pinC >= 0 ? pinC : hoverC;
    var has = aR >= 0;
    for (var ii = 0; ii < N; ii++) {
      for (var jj = 0; jj < N; jj++) {
        var c = cellEls[ii][jj];
        var isPin = (pinR === ii && pinC === jj);
        var isHov = (hoverR === ii && hoverC === jj);
        var inLine = has && (aR === ii || aC === jj);
        c.style.border = isPin ? "2px solid #38BDF8" : isHov ? "1px solid rgba(56,189,248,0.5)" : inLine ? "1px solid rgba(56,189,248,0.18)" : "1px solid transparent";
        c.style.transform = isHov ? "scale(1.14)" : "scale(1)";
        c.style.opacity = (has && !inLine && !isPin) ? "0.38" : "1";
        c.style.zIndex = isHov ? "2" : "1";
      }
    }
    var rowLabels = root.querySelectorAll(".hm-row-label");
    rowLabels.forEach(function(el) {
      var r = parseInt(el.getAttribute("data-row"));
      el.style.color = (has && r === aR) ? "#38BDF8" : "#64748B";
      el.style.fontWeight = (has && r === aR) ? "700" : "400";
    });
    var colLabels = root.querySelectorAll(".hm-col-label");
    colLabels.forEach(function(el, j) {
      el.style.color = (has && j === aC) ? "#38BDF8" : "#475569";
      el.style.fontWeight = (has && j === aC) ? "700" : "400";
    });
    pairEls.forEach(function(p) {
      var act = (hoverR===p.a&&hoverC===p.b)||(hoverR===p.b&&hoverC===p.a)||(pinR===p.a&&pinC===p.b)||(pinR===p.b&&pinC===p.a);
      p.el.style.background = act ? "rgba(56,189,248,0.08)" : "transparent";
    });
    if (!has) {
      detailCard.style.background = "rgba(255,255,255,0.02)";
      detailCard.style.borderColor = "#1E293B";
      detailCard.innerHTML = '<div style="color:#334155;font-size:12px;line-height:1.8;">悬停格子查看共现详情<br>点击可固定显示<div style="margin-top:10px;font-size:10px;color:#1E3A5A;line-height:1.6;">数据来源：CANGO 海外资源库<br>2026年3月 · 202 家机构<br>MECE 清洗：157 → 12 类</div></div>';
      return;
    }
    var val = MATRIX[aR][aC];
    var isDiag = (aR === aC);
    detailCard.style.background = "rgba(56,189,248,0.06)";
    detailCard.style.borderColor = "#38BDF8";
    if (isDiag) {
      var pct = Math.round(val / maxDiag * 100);
      detailCard.innerHTML = '<div style="font-size:10px;color:#A78BFA;font-weight:700;margin-bottom:6px;letter-spacing:1px;">📌 单类别总量</div><div style="font-size:28px;font-weight:900;color:#F1F5F9;">'+val+'<span style="font-size:13px;color:#64748B;margin-left:4px;">家机构</span></div><div style="font-size:13px;font-weight:700;color:#A78BFA;margin:6px 0 8px;">'+TOPICS[aR]+'</div><div style="height:3px;background:#1E293B;border-radius:2px;margin-bottom:6px;"><div style="height:100%;border-radius:2px;background:#A78BFA;width:'+pct+'%;"></div></div><div style="font-size:10px;color:#475569;line-height:1.5;">'+MECE_NOTE[TOPICS[aR]]+'</div>';
    } else {
      var pctR = Math.round(val / MATRIX[aR][aR] * 100);
      var pctC = Math.round(val / MATRIX[aC][aC] * 100);
      detailCard.innerHTML = '<div style="font-size:10px;color:#38BDF8;font-weight:700;margin-bottom:5px;letter-spacing:1px;">🔗 议题共现</div><div style="font-size:30px;font-weight:900;color:#F1F5F9;">'+val+'<span style="font-size:13px;color:#64748B;margin-left:4px;">家机构</span></div><div style="font-size:11px;color:#64748B;margin:4px 0 8px;">同时关注以下两类议题</div><div style="display:flex;flex-direction:column;gap:5px;margin-bottom:10px;"><div style="background:rgba(56,189,248,0.1);border-radius:6px;padding:5px 10px;font-size:11px;color:#38BDF8;font-weight:600;">✦ '+TOPICS[aR]+'</div><div style="text-align:center;font-size:10px;color:#334155;">同时关注</div><div style="background:rgba(45,212,191,0.1);border-radius:6px;padding:5px 10px;font-size:11px;color:#2DD4BF;font-weight:600;">✦ '+TOPICS[aC]+'</div></div><div style="display:flex;gap:14px;"><div><div style="font-size:9px;color:#475569;">占「'+SHORT[aR]+'」</div><div style="font-size:13px;font-weight:700;color:#CBD5E1;">'+pctR+'%</div></div><div><div style="font-size:9px;color:#475569;">占「'+SHORT[aC]+'」</div><div style="font-size:13px;font-weight:700;color:#CBD5E1;">'+pctC+'%</div></div></div>';
    }
  }
  } // end runHeatmap
  if (document.readyState !== "loading") runHeatmap();
  else document.addEventListener("DOMContentLoaded", runHeatmap);
})();

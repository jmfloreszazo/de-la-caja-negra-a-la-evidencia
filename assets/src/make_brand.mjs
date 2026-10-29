// JMFLORESZAZO v5 design system — approved principal symbol and compact variant B.
// Generated assets are deterministic; requires Node.js 22+, no external runtime fonts.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
const COLORS={"ink":"#121315","dark":"#0E1012","paper":"#F7F7F5","white":"#FFFFFF","red":"#D9232E","grey":"#797E83","muted":"#565C62","stroke":"#D5D8DA"};
function doc(w,h,body,bg){return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" role="img">${bg?`<rect width="${w}" height="${h}" fill="${bg}"/>`:""}${body}</svg>\n`;}

function tx(x,y,t,size,c=COLORS.ink,weight=400,spacing=0,anchor="start"){let e=t.replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;");return `<text x="${x}" y="${y}" font-family="Arial,Helvetica,sans-serif" font-size="${size}" font-weight="${weight}" fill="${c}" letter-spacing="${spacing}" text-anchor="${anchor}">${e}</text>`;}

function primary(){
 const edges=[[368,302,417,278],[417,278,474,324],[474,324,533,272],[368,302,351,365],[351,365,415,393],[415,393,474,324],[415,393,474,445],[474,445,537,392],[537,392,533,272],[351,365,376,448],[376,448,474,445],[417,278,461,232],[461,232,533,272],[415,393,537,392],[474,324,537,392]];
 const nodes=[[368,302],[417,278],[474,324],[533,272],[351,365],[415,393],[474,445],[537,392],[376,448],[461,232]];
 return `<g stroke-linejoin="round">
 <path d="M126 172 L366 64 L594 150 L351 262 Z" fill="#222427"/>
 <path d="M126 172 L351 262 L351 548 L126 455 Z" fill="#111214"/>
 <path d="M351 262 L594 150 L594 432 L351 548 Z" fill="#1A1C1F"/>
 <path d="M126 172 L366 64 L594 150 L594 432 L351 548 L126 455 Z" fill="none" stroke="#878B8E" stroke-width="2"/>
 <path d="M126 172 L351 262 L594 150 M351 262 V548" fill="none" stroke="#C0C3C4" stroke-width="2"/>
 <g stroke="#60666B" stroke-width="2" fill="none" opacity=".96">${edges.map(([a,b,c,d])=>`<line x1="${a}" y1="${b}" x2="${c}" y2="${d}"/>`).join("")}</g>
 <g fill="#888E92">${nodes.map(([a,b])=>`<circle cx="${a}" cy="${b}" r="7.5"/>`).join("")}</g>
 <path d="M409 351 L481 414 L568 413 L693 351 L832 351" fill="none" stroke="${COLORS.red}" stroke-width="11" stroke-linecap="round" stroke-linejoin="round"/>
 <g fill="${COLORS.red}"><circle cx="409" cy="351" r="13"/><circle cx="481" cy="414" r="13"/><circle cx="693" cy="351" r="14"/></g>
 <path d="M661 199 L759 151 L759 301 M759 402 V485 L661 535 L661 401" fill="none" stroke="#151719" stroke-width="12" stroke-linecap="square"/>
 <path d="M832 327 L867 351 L832 375 Z" fill="${COLORS.red}"/></g>`;
}

function iconB(dark=false){let shell=dark?"#F3F3F1":"#181A1C",face=dark?"#C6C9CB":"#25282B",gate=dark?"#F3F3F1":"#181A1C";
 return `<g stroke-linejoin="round"><path d="M53 156 L206 85 L270 117 L117 188 Z" fill="${face}"/>
 <path d="M53 156 L117 188 L117 392 L53 355 Z" fill="${shell}"/>
 <path d="M117 188 L270 117 L270 320 L117 392 Z" fill="${shell}"/>
 <path d="M53 156 L206 85 L270 117 L270 320 L117 392 L53 355 Z" fill="none" stroke="${gate}" stroke-width="3"/>
 <path d="M294 150 L338 130 L338 236 M338 303 L338 371 L294 394 L294 303" fill="none" stroke="${gate}" stroke-width="13" stroke-linecap="square"/>
 <path d="M265 270 H430" stroke="${COLORS.red}" stroke-width="14" stroke-linecap="round"/>
 <circle cx="411" cy="270" r="18" fill="${COLORS.red}"/><path d="M445 245 L485 270 L445 295 Z" fill="${COLORS.red}"/></g>`;
}

function lockup(lang,dark){
 let t=lang==="es"?["DE LA CAJA NEGRA","A LA EVIDENCIA"]:["FROM BLACK BOX","TO EVIDENCE"];
 let fg=dark?COLORS.white:COLORS.ink,sub=dark?"#B7BDC0":COLORS.muted;
 return doc(1120,265,`<g transform="scale(.58)">${iconB(dark)}</g>`+tx(290,105,t[0],72,fg,800,-1.5)+tx(290,185,t[1],72,COLORS.red,800,-1.5)+tx(292,237,"JMFLORESZAZO / ARCHITECTING WHAT'S NEXT",19,sub,700,1.9));
}

function cover(lang){
 let es=lang==="es",t1=es?"De la caja negra":"From Black Box",t2=es?"a la evidencia":"to Evidence";
 let s1=es?"Modernizar COBOL más allá":"Modernizing COBOL beyond",s2=es?"de la traducción":"translation";
 let ed=es?"EDICIÓN v2026.10.29":"EDITION v2026.10.29";
 let b=tx(136,144,"JMFLORESZAZO",37,COLORS.ink,800,5)+
 `<path d="M1365 126 H1460" stroke="${COLORS.red}" stroke-width="9"/>`+
 tx(1280,140,"ARCHITECTING WHAT'S NEXT",23,COLORS.ink,700,2.5,"end")+
 `<path d="M132 185 H1468" stroke="${COLORS.stroke}" stroke-width="2"/>`+
 tx(134,392,t1,126,COLORS.ink,800,-4.5)+tx(134,538,t2,126,COLORS.red,800,-4.5)+
 tx(137,641,s1,53,COLORS.muted,400,-.6)+tx(137,708,s2,53,COLORS.muted,400,-.6)+
 `<g transform="translate(0 620) scale(1.6)">${primary()}</g>`+
 `<path d="M132 2135 H1468" stroke="${COLORS.stroke}" stroke-width="2"/>`+
 tx(134,2210,"JOSÉ MARÍA FLORES ZAZO",34,COLORS.ink,700,2.2)+
 tx(1465,2210,ed,27,COLORS.grey,600,2,"end")+
 tx(134,2295,"LEGACY / ARCHITECTURE / EVIDENCE",22,COLORS.grey,600,3);
 return doc(1600,2400,b,COLORS.paper);
}

function social(){
 let b=tx(76,74,"JMFLORESZAZO",26,COLORS.ink,800,3)+
 `<path d="M1221 57 H1255" stroke="${COLORS.red}" stroke-width="7"/>`+
 tx(1208,72,"ARCHITECTING WHAT'S NEXT",17,COLORS.ink,700,1.7,"end")+
 tx(76,223,"De la caja negra",73,COLORS.ink,800,-2)+tx(76,310,"a la evidencia",73,COLORS.red,800,-2)+
 tx(78,373,"Modernizar COBOL más allá de la traducción",27,COLORS.muted)+
 `<g transform="translate(705 92) scale(.53)">${primary()}</g>`+
 `<path d="M76 510 H1204" stroke="${COLORS.stroke}" stroke-width="2"/>`+
 tx(77,554,"FROM BLACK BOX TO EVIDENCE / OPEN BOOK ES + EN / RUNNABLE LAB",18,COLORS.muted,700,1);
 return doc(1280,640,b,COLORS.paper);
}

function assets(){
 return {
 "symbol-primary.svg":doc(1000,620,primary()),
 "mark.svg":doc(512,512,iconB()),
 "icon-b-dark.svg":doc(512,512,iconB(true)),
 "logo-es-light.svg":lockup("es",false),
 "logo-es-dark.svg":lockup("es",true),
 "logo-en-light.svg":lockup("en",false),
 "logo-en-dark.svg":lockup("en",true),
 "cover-es.svg":cover("es"),
 "cover-en.svg":cover("en"),
 "social-preview.svg":social()
 };
}
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const check=process.argv.includes("--check");
let stale=[];
for(const [name,content] of Object.entries(assets())){
 const target=path.join(root,name);
 if(check){if(!fs.existsSync(target)||fs.readFileSync(target,"utf8")!==content)stale.push(name);}
 else{fs.writeFileSync(target,content,"utf8");process.stdout.write("svg "+name+"\n");}
}
if(stale.length){process.stderr.write("STALE BRAND SVG: "+stale.join(", ")+"\n");process.exitCode=1;}
else if(check)process.stdout.write("BRAND SVG: PASS\n");

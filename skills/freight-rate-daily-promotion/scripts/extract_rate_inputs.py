#!/usr/bin/env python3
"""Extract basic text/tables from 运价表 xlsx and 运价信息 docx without third-party deps.
Outputs normalized-ish JSON and a Markdown digest for human/agent review.
"""
import argparse, json, re, zipfile, html, os
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET

PRICE_RE = re.compile(r'(?<!\w)(?:USD|US\$|RMB|CNY|￥|\$)?\s*-?\d{2,6}(?:\.\d+)?(?!\w)', re.I)
BOX_RE = re.compile(r'20\s*(?:GP|FT|\')|40\s*(?:GP|HQ|FT|\')|HQ|小柜|大柜|高柜', re.I)
COST_RE = re.compile(r'成本|底价|拿价|采购价|cost|net|buy', re.I)
SELL_RE = re.compile(r'卖价|报价|对外|销售价|sell|selling|offer|quote', re.I)
ROUTE_HINT_RE = re.compile(r'红海|中东|印巴|印度|巴基斯坦|东南亚|美线|美国|欧洲|欧地|非洲|地中海|澳洲|日韩|航线')

NS_MAIN = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
NS_REL = '{http://schemas.openxmlformats.org/package/2006/relationships}'


def text_of_docx(path: Path):
    paras=[]
    with zipfile.ZipFile(path) as z:
        data=z.read('word/document.xml')
    root=ET.fromstring(data)
    ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    for p in root.findall('.//w:p', ns):
        txt=''.join(t.text or '' for t in p.findall('.//w:t', ns)).strip()
        if txt:
            paras.append(txt)
    return paras


def col_letters_to_idx(ref):
    letters=''.join(ch for ch in ref if ch.isalpha())
    n=0
    for ch in letters:
        n=n*26+ord(ch.upper())-64
    return n-1


def read_shared_strings(z):
    try:
        root=ET.fromstring(z.read('xl/sharedStrings.xml'))
    except KeyError:
        return []
    out=[]
    for si in root.findall(f'.//{NS_MAIN}si'):
        out.append(''.join(t.text or '' for t in si.findall(f'.//{NS_MAIN}t')))
    return out


def workbook_sheets(z):
    wb=ET.fromstring(z.read('xl/workbook.xml'))
    rels=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    rid_to_target={r.attrib['Id']: r.attrib['Target'] for r in rels.findall(f'.//{NS_REL}Relationship')}
    sheets=[]
    for s in wb.findall(f'.//{NS_MAIN}sheet'):
        name=s.attrib.get('name','Sheet')
        rid=s.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
        target=rid_to_target.get(rid,'')
        if target and not target.startswith('xl/'):
            target='xl/'+target
        sheets.append((name,target))
    return sheets


def read_xlsx(path: Path):
    sheets=[]
    with zipfile.ZipFile(path) as z:
        shared=read_shared_strings(z)
        for name,target in workbook_sheets(z):
            try:
                root=ET.fromstring(z.read(target))
            except KeyError:
                continue
            rows=[]
            for row in root.findall(f'.//{NS_MAIN}row'):
                vals=[]
                for c in row.findall(f'{NS_MAIN}c'):
                    idx=col_letters_to_idx(c.attrib.get('r','A1'))
                    while len(vals)<=idx:
                        vals.append('')
                    v=c.find(f'{NS_MAIN}v')
                    txt=''
                    if v is not None and v.text is not None:
                        if c.attrib.get('t')=='s':
                            try: txt=shared[int(v.text)]
                            except Exception: txt=v.text
                        else:
                            txt=v.text
                    vals[idx]=txt.strip() if isinstance(txt,str) else str(txt)
                if any(x for x in vals):
                    rows.append(vals)
            sheets.append({'name':name,'rows':rows})
    return sheets


def classify_line(text):
    prices=PRICE_RE.findall(text)
    if not prices:
        return None
    klass='unknown'
    if COST_RE.search(text): klass='cost'
    if SELL_RE.search(text): klass='sell' if klass=='unknown' else 'mixed'
    return {'text':text, 'prices':[p.strip() for p in prices], 'price_type':klass, 'route_hint': bool(ROUTE_HINT_RE.search(text)), 'box_hint': bool(BOX_RE.search(text))}


def extract_from_xlsx(path):
    items=[]
    for sheet in read_xlsx(path):
        rows=sheet['rows']
        for i,row in enumerate(rows, start=1):
            joined=' | '.join(str(x) for x in row if str(x).strip())
            if not joined: continue
            hit=classify_line(joined)
            if hit:
                hit.update({'source_file':path.name,'source_type':'xlsx','sheet':sheet['name'],'row':i})
                items.append(hit)
    return items


def extract_from_docx(path):
    items=[]
    for i,p in enumerate(text_of_docx(path), start=1):
        hit=classify_line(p)
        if hit:
            hit.update({'source_file':path.name,'source_type':'docx','paragraph':i})
            items.append(hit)
    return items


def latest_matching(input_dir, patterns):
    files=[]
    for pat in patterns:
        files += list(Path(input_dir).glob(pat))
    return sorted(set(files), key=lambda p:p.stat().st_mtime, reverse=True)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input-dir', default='.')
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--xlsx', action='append', default=[])
    ap.add_argument('--docx', action='append', default=[])
    args=ap.parse_args()
    out=Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
    xlsx=[Path(p) for p in args.xlsx] or latest_matching(args.input_dir, ['运价表*.xlsx','*运价表*.xlsx'])[:1]
    docx=[Path(p) for p in args.docx] or latest_matching(args.input_dir, ['运价信息*.docx','*运价信息*.docx'])[:1]
    items=[]; errors=[]
    for p in xlsx:
        try: items += extract_from_xlsx(p)
        except Exception as e: errors.append({'file':str(p),'error':str(e)})
    for p in docx:
        try: items += extract_from_docx(p)
        except Exception as e: errors.append({'file':str(p),'error':str(e)})
    summary={
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'sources': [str(p) for p in xlsx+docx],
        'counts': {
            'items': len(items),
            'xlsx_items': sum(1 for x in items if x['source_type']=='xlsx'),
            'docx_items': sum(1 for x in items if x['source_type']=='docx'),
            'cost': sum(1 for x in items if x['price_type'] in ('cost','mixed')),
            'sell': sum(1 for x in items if x['price_type'] in ('sell','mixed')),
            'unknown': sum(1 for x in items if x['price_type']=='unknown'),
        },
        'errors': errors,
        'items': items,
    }
    (out/'daily-rate-extract.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    lines=[f"# Daily Rate Extract - {summary['generated_at']}", '', '## Sources', *[f'- {s}' for s in summary['sources']], '', '## Counts', *[f'- {k}: {v}' for k,v in summary['counts'].items()], '']
    if errors:
        lines += ['## Errors', *[f"- {e['file']}: {e['error']}" for e in errors], '']
    lines += ['## Extracted price lines']
    for it in items[:300]:
        ref=f"{it['source_file']}"
        if it['source_type']=='xlsx': ref += f" / {it.get('sheet')} row {it.get('row')}"
        else: ref += f" / paragraph {it.get('paragraph')}"
        lines.append(f"- [{it['price_type']}] {ref}: {it['text']}")
    (out/'daily-rate-extract.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({'ok': True, 'out_dir': str(out), 'counts': summary['counts'], 'errors': errors}, ensure_ascii=False))

if __name__=='__main__':
    main()

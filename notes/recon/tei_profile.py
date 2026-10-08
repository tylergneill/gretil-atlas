import re, glob, collections, os
years = collections.Counter(); refs = 0; noref = []; langs = collections.Counter(); authors = collections.Counter(); sizes = []
for f in sorted(glob.glob('*.xml')):
    s = open(f, encoding='utf-8', errors='replace').read()
    h = s[:s.find('</teiHeader>')] if '</teiHeader>' in s else s[:20000]
    m = re.search(r'<date when-iso="(\d{4})', h); years[m.group(1) if m else 'none'] += 1
    r = re.search(r'<ref target="[^"]*/(\w+\.htm)"', h)
    if r: refs += 1
    else: noref.append(f)
    a = re.search(r'<author>([^<]*)</author>', h); authors[(a.group(1).strip() if a else '(none)')] += 1
    sizes.append(os.path.getsize(f))
print('xml files', len(sizes), 'with <ref> to legacy htm', refs, 'without', len(noref))
print('no-ref sample', noref[:8])
print('publication date years', sorted(years.items()))
print('authors top', authors.most_common(12))
print('total xml bytes GB', sum(sizes)/1e9)
pt = glob.glob('transformations/plaintext/*.txt'); print('plaintext txt', len(pt), 'bytes GB', sum(os.path.getsize(p) for p in pt)/1e9)

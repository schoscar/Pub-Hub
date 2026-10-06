# Copies the app's vocabulary (teams, features, cuisines) into the Worker so the
# model is only ever offered values the app can actually filter on.
import json, re, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
html = open(os.path.join(root, 'index.html'), encoding='utf-8').read()
teams = dict(re.findall(r'\["([A-Z]{3})", "([^"]+)", "(?:London|Rest of the UK|International)"\]', html))
feat_block = re.search(r'const FEAT = \{(.*?)\};', html).group(1)
features = re.findall(r'(\w+): "', feat_block) + ["outdoor"]
pubs = json.load(open(os.path.join(root, 'data', 'pubs_plus.json')))
from collections import Counter
c = Counter(x for p in pubs for x in p['food']['cuisine'])
cuisines = sorted(k for k, n in c.items() if n >= 3 and k not in ('Bar snacks', 'Local', 'International'))
vocab = {"teams": teams, "features": features, "cuisines": cuisines}
path = os.path.join(root, 'worker', 'pub-hub-ask.js')
src = open(path, encoding='utf-8').read()
src = re.sub(r'/\*VOCAB-START\*/.*?/\*VOCAB-END\*/',
             '/*VOCAB-START*/\nconst VOCAB = ' + json.dumps(vocab, ensure_ascii=True) + ';\n/*VOCAB-END*/', src, flags=re.S)
open(path, 'w', encoding='utf-8').write(src)
print(len(teams), 'teams,', len(features), 'features,', len(cuisines), 'cuisines')

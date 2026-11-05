"""Check public chemical evidence and conservative activity links."""
import json
from pathlib import Path
from build_chemicals import identity, check_link_boundaries

ROOT = Path(__file__).resolve().parents[1]
read = lambda path: json.loads((ROOT / path).read_text(encoding='utf-8-sig'))
chemicals = read('site/dist/data/chemicals.json')
materials = read('site/dist/data/materials.json')
activities = read('site/dist/data/activities.json')
guidelines = read('site/dist/data/chemical_guidelines.json')
source_pages = {}
for path in (ROOT / 'output/parsed').glob('*.json'):
    import re
    source = json.loads(path.read_text(encoding='utf-8-sig'))
    for section in source['sections']:
        page = int(re.search(r'인쇄면 (\d+)쪽', section['heading'])[1])
        source_pages[(source['source_file'], page)] = section['content_markdown']

def check_reference(ref):
    original = source_pages[(ref['file'], ref['print_page'])]
    assert ref['raw_text'] in original
    return original

assert len(chemicals) == 177
by_id = {c['id']: c for c in chemicals}
assert len(by_id) == len(chemicals)
fields = {'classifications': ('group', 'label'), 'storage': ('property', 'instruction'),
          'cabinets': ('name', 'category', 'qualifier'), 'incompatibilities': ('materials_raw',)}
for chemical in chemicals:
    assert chemical['pictograms'] is None and chemical['disposal'] is None
    for ref in chemical['source_refs']:
        check_reference(ref)
    for field, keys in fields.items():
        for row in chemical[field]:
            source = check_reference(row['source_ref'])
            for key in keys:
                assert row.get(key) is None or row[key] in source, (chemical['name'], key)

by_name = {c['name']: c for c in chemicals}
assert by_name['페놀프탈레인 용액']['cabinets'] == []
assert by_name['암모니아수']['incompatibilities'] == []
assert by_name['암모니아']['incompatibilities']
assert by_name['수산화 칼슘']['storage'] == [] and by_name['석회수']['storage']
assert by_name['염화 나트륨']['storage'] == []
assert not any('갈색 병' in row['instruction'] for row in by_name['아이오딘']['storage'])
assert any('갈색 병' in row['instruction'] for row in by_name['아이오딘 용액']['storage'])
assert by_name['알칼리 금속(Li, Na, K)']['formula'] is None
by_activity = {a['id']: a for a in activities}
by_material = {m['id']: m for m in materials}
for material in materials:
    chemical = by_id[material['chemical_id']]
    aliases = {identity(n) for n in [chemical['name'], *chemical['aliases']]}
    for mention in material['source_mentions']:
        activity = by_activity[mention['activity_id']]
        assert mention['raw_text'] == activity['materials_raw']
        assert mention['source_row'] == activity['source_row']
        assert mention['matched_text'] in activity['materials_raw']
        assert identity(mention['matched_text']) in aliases
        assert material['id'] in activity['material_ids']
        assert chemical['id'] in activity['chemical_ids']
for activity in activities:
    assert len(set(activity['chemical_ids'])) == len(activity['chemical_ids'])
    assert {by_material[mid]['chemical_id'] for mid in activity['material_ids']} == set(activity['chemical_ids'])
assert len(guidelines) == 6
assert {g['source_ref']['print_page'] for g in guidelines} == {16, 17, 21, 22, 23, 25}
for guide in guidelines:
    assert guide['content_markdown'] == guide['source_ref']['raw_text']
    check_reference(guide['source_ref'])
check_link_boundaries(ROOT)
print(json.dumps({'status': 'passed', 'catalogue': len(chemicals), 'linked_materials': len(materials),
                  'linked_activities': sum(bool(a['chemical_ids']) for a in activities),
                  'guidelines': len(guidelines), 'boundary_fixtures': 16}))

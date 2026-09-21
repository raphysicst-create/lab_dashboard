"""Read-only verification of exported review workbook against immutable JSON."""
from pathlib import Path
import hashlib
import json
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'science_experiment_supplies.json'
OUT = ROOT / 'outputs' / 'review'
BOOK = OUT / 'science_experiment_review.xlsx'
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
KEYS = ['id', 'source_row', '단원명', '성취기준', '출판사', '쪽', '탐구활동', '교구']
source_bytes = SOURCE.read_bytes()
source = json.loads(source_bytes.decode('utf-8-sig'))

with zipfile.ZipFile(BOOK) as archive:
    shared = []
    if 'xl/sharedStrings.xml' in archive.namelist():
        shared_xml = ET.fromstring(archive.read('xl/sharedStrings.xml'))
        shared = [''.join(si.itertext()) for si in shared_xml.findall('s:si', NS)]
    sheet = ET.fromstring(archive.read('xl/worksheets/sheet1.xml'))
    cells = {cell.attrib['r']: cell for cell in sheet.findall('.//s:sheetData/s:row/s:c', NS)}

    def cell_value(address):
        cell = cells.get(address)
        if cell is None:
            return None
        assert cell.find('s:f', NS) is None, f'Unexpected formula in {address}'
        cell_type = cell.attrib.get('t')
        value = cell.find('s:v', NS)
        if cell_type == 'inlineStr':
            return ''.join(cell.find('s:is', NS).itertext())
        if value is None or value.text is None:
            return None
        if cell_type == 's':
            return shared[int(value.text)]
        if cell_type == 'str':
            return value.text
        number = float(value.text)
        return int(number) if number.is_integer() else number

    assert len(source['data']) == 454
    assert len({row['id'] for row in source['data']}) == 454
    for row_index, row in enumerate(source['data'], start=6):
        for col_index, key in enumerate(KEYS):
            address = f'{chr(65 + col_index)}{row_index}'
            actual = cell_value(address)
            expected = row[key]
            assert actual == expected, f'{address}: {actual!r} != {expected!r}'
        assert [cell_value(f'{col}{row_index}') for col in 'IJKL'] == ['미확인'] * 4
        assert cell_value(f'M{row_index}') == '교과서 대조 미확인'
        assert all(cell_value(f'{col}{row_index}') is None for col in 'NOPQRSTUVW')

    assert all(cell_value(f'{col}5') == key for col, key in zip('ABCDEFGH', KEYS))
    pane = sheet.find('s:sheetViews/s:sheetView/s:pane', NS)
    assert pane is not None and pane.attrib.get('state') == 'frozen'
    assert float(pane.attrib.get('xSplit', '0')) == 2, pane.attrib
    assert float(pane.attrib.get('ySplit', '0')) == 5, pane.attrib
    validations = sheet.findall('s:dataValidations/s:dataValidation', NS)
    assert {v.attrib['sqref'] for v in validations} == {'M6:M459', 'J6:J459'}
    assert all(v.attrib.get('type') == 'list' for v in validations)
    tables = [name for name in archive.namelist() if name.startswith('xl/tables/') and name.endswith('.xml')]
    assert len(tables) == 1
    table = ET.fromstring(archive.read(tables[0]))
    assert table.attrib['ref'] == 'A5:W459'
    assert table.find('s:autoFilter', NS).attrib['ref'] == 'A5:W459'
    assert len(table.findall('s:tableColumns/s:tableColumn', NS)) == 23
    workbook = ET.fromstring(archive.read('xl/workbook.xml'))
    sheet_names = [s.attrib['name'] for s in workbook.findall('s:sheets/s:sheet', NS)]
    assert sheet_names == ['탐구활동 검토', '검토 방법']
    all_sheet_names = [name for name in archive.namelist() if name.startswith('xl/worksheets/sheet') and name.endswith('.xml')]
    for name in all_sheet_names:
        xml = ET.fromstring(archive.read(name))
        assert not xml.findall('.//s:f', NS), f'Unexpected executable formula in {name}'
    assert not archive.namelist().count('xl/vbaProject.bin')

report = {
    'workbook': str(BOOK),
    'records': 454,
    'source_cells_exactly_equal': 454 * 8,
    'missing_supplies_cells_preserved': sum(row['교구'] is None for row in source['data']),
    'unknown_review_rows': 454,
    'official_mapping_fields_unknown': 454 * 4,
    'native_filter': 'A5:W459',
    'native_frozen_rows': 5,
    'native_frozen_columns': 2,
    'native_validation_ranges': ['M6:M459', 'J6:J459'],
    'formula_cells': 0,
    'worksheets': sheet_names,
    'source_json_sha256': hashlib.sha256(source_bytes).hexdigest(),
    'result': 'passed',
}
(OUT / 'xlsx-validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False))

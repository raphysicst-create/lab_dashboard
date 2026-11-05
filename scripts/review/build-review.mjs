import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const here = path.dirname(fileURLToPath(import.meta.url));
const workspace = path.resolve(here, '../..');
const sourcePath = path.resolve(workspace, 'science_experiment_supplies.json');
const outputDir = path.resolve(workspace, 'outputs/review');
const outputPath = path.join(outputDir, 'science_experiment_review.xlsx');
const replace = process.argv.includes('--replace');
try {
  await fs.access(outputPath);
  if (!replace) throw new Error('검토표가 이미 있습니다. 작성한 검토 내용을 백업한 뒤 --replace 옵션으로 재생성하세요.');
} catch (error) {
  if (error.code !== 'ENOENT') throw error;
}
await fs.mkdir(outputDir, { recursive: true });
const sourceBytes = await fs.readFile(sourcePath);
const source = JSON.parse(sourceBytes.toString('utf8').replace(/^\uFEFF/, ''));
const originalKeys = ['id', 'source_row', ...source.metadata.original_columns];
assert.deepEqual(originalKeys, ['id', 'source_row', '단원명', '성취기준', '출판사', '쪽', '탐구활동', '교구']);
assert.equal(source.data.length, 454);
assert.equal(new Set(source.data.map(row => row.id)).size, 454);
const sha256 = crypto.createHash('sha256').update(sourceBytes).digest('hex');
const headerRow = 5;
const firstRow = 6;
const lastRow = firstRow + source.data.length - 1;
const headers = [...originalKeys, '공식 성취기준 코드', '학년', '교과서명', '판본', '교과서 대조 상태', '대조 근거 / 위치', '수정 단원명', '수정 성취기준', '수정 출판사', '수정 쪽', '수정 탐구활동', '수정 교구', '검토자', '검토일', '검토 메모'];
// Writing through values plus text formats preserves literal source data. Leading
// formula introducers are escaped before entering Excel, never run as formulas.
const literal = value => typeof value === 'string' && /^[=+@\-]/.test(value) ? `'${value}` : value;
const rows = source.data.map(row => [
  ...originalKeys.map(key => literal(row[key])),
  '미확인', '미확인', '미확인', '미확인', '교과서 대조 미확인',
  null, null, null, null, null, null, null, null, null, null,
]);

const workbook = Workbook.create();
const review = workbook.worksheets.add('탐구활동 검토');
const guide = workbook.worksheets.add('검토 방법');
review.showGridLines = false;
guide.showGridLines = false;
review.tabColor = '#304967';
guide.tabColor = '#8393A4';
review.getRange(`A1:W${lastRow}`).format.font = { name: 'Malgun Gothic', size: 11, color: '#172B40' };
review.getRange(`A5:W${lastRow}`).format.verticalAlignment = 'top';
review.getRange(`A6:W${lastRow}`).format.wrapText = true;
review.getRange(`A6:W${lastRow}`).setNumberFormat('@');
review.getRange(`B6:B${lastRow}`).setNumberFormat('0');
review.getRange(`F6:F${lastRow}`).setNumberFormat('0');
review.getRange(`R6:R${lastRow}`).setNumberFormat('0');
review.getRange(`V6:V${lastRow}`).setNumberFormat('yyyy-mm-dd');
review.getRange(`A5:W${lastRow}`).values = [headers, ...rows];
review.getRange('A2').values = [['중학교 과학 탐구·실험 준비물 검토표']];
review.getRange('A2').format.font = { name: 'Malgun Gothic', size: 15, bold: true };
review.getRange('A2:W2').format.rowHeight = 28;
review.getRange('A3:W4').format.rowHeight = 24;
review.getRange('A3').values = [[`출처: science_experiment_supplies.json / ${source.metadata.primary_sheet} / 454행. 원자료 변환만 완료. 교과서 대조 미확인.`]];
review.getRange('A3').format.font = { name: 'Malgun Gothic', size: 11, italic: true, color: '#536478' };
review.getRange('A4').values = [['A:H 원문 보존 · I:W 검토 입력 · 수정값은 사이트에 자동 반영되지 않습니다.']];
review.getRange('A4').format.font = { name: 'Malgun Gothic', size: 11, color: '#536478' };
const table = review.tables.add(`A5:W${lastRow}`, true, 'ExperimentReview');
table.showFilterButton = true;
table.showTotals = false;
review.getRange('A5:H5').format.fill = '#304967';
review.getRange('I5:W5').format.fill = '#6F5219';
review.getRange('A5:W5').format.font = { name: 'Malgun Gothic', size: 11, bold: true, color: '#FFFFFF' };
review.getRange('A5:W5').format.horizontalAlignment = 'center';
review.getRange('A5:W5').format.verticalAlignment = 'center';
review.getRange('A5:W5').format.wrapText = true;
review.getRange('A5:W5').format.rowHeight = 42;
review.getRange('A5:W5').format.borders = { insideVertical: { style: 'thin', color: '#FFFFFF' } };
review.getRange(`I6:W${lastRow}`).format.fill = '#FFF9E8';
review.getRange(`A6:H${lastRow}`).format.fill = '#F4F7FA';
const widths = [19, 13, 27, 64, 22, 8, 46, 86, 26, 13, 31, 22, 29, 46, 27, 64, 22, 11, 46, 86, 18, 16, 55];
for (let col = 0; col < widths.length; col++) {
  review.getRangeByIndexes(0, col, lastRow, 1).format.columnWidth = widths[col];
}
// Fit each original record without changing source text or hiding line breaks.
for (let index = 0; index < rows.length; index++) {
  let lineCount = 1;
  for (let col = 0; col < 8; col++) {
    const value = rows[index][col];
    if (value === null) continue;
    const effectiveChars = Math.max(8, Math.floor(widths[col] / 1.85));
    const lines = String(value).split('\n').reduce((sum, line) => sum + Math.max(1, Math.ceil(line.length / effectiveChars)), 0);
    lineCount = Math.max(lineCount, lines);
  }
  review.getRangeByIndexes(index + firstRow - 1, 0, 1, headers.length).format.rowHeight = Math.max(42, lineCount * 17 + 10);
}
review.getRange(`B6:B${lastRow}`).format.horizontalAlignment = 'right';
review.getRange(`F6:F${lastRow}`).format.horizontalAlignment = 'right';
review.getRange(`R6:R${lastRow}`).format.horizontalAlignment = 'right';
review.getRange(`V6:V${lastRow}`).format.horizontalAlignment = 'right';
review.getRange(`M6:M${lastRow}`).dataValidation = { rule: { type: 'list', values: ['교과서 대조 미확인', '대조 중', '수정 필요', '대조 완료'] } };
review.getRange(`J6:J${lastRow}`).dataValidation = { rule: { type: 'list', values: ['미확인', '1', '2', '3'] } };
review.getRange(`M6:M${lastRow}`).conditionalFormats.add('containsText', { text: '미확인', format: { fill: '#FFF0CA', font: { color: '#75470E' } } });
review.getRange(`M6:M${lastRow}`).conditionalFormats.add('containsText', { text: '수정 필요', format: { fill: '#FDE9E7', font: { color: '#9C2B24', bold: true } } });
review.freezePanes.freezeRows(headerRow);
review.freezePanes.freezeColumns(2);

const guideRows = [
  ['검토 대상', '2022 개정 교육과정 중학교 과학 교과서 탐구·실험 준비물 자료 454행'],
  ['최초 상태', '원자료 변환만 완료했습니다. 454행 모두 교과서 대조 미확인입니다.'],
  ['최우선 원칙', '근거로 확인하지 못한 실험 정보는 임의로 작성하지 않습니다. 원문에 없는 정보는 미확인으로 남깁니다.'],
  ['공개 범위', '이 파일은 작업 공간의 내부 검토표입니다. 교과서 대조 미확인 상태와 검토 기록을 공개 사이트에 배포하지 않습니다.'],
  ['원문 보존', 'A:H 열은 id, source_row와 원본 6열입니다. 문자열·공백·줄바꿈·오탈자·null(빈 셀)을 보존합니다. 원문 열을 직접 수정하지 마세요.'],
  ['행 연결', 'id가 행의 고유 식별자입니다. source_row는 원본 기본자료 시트의 행 번호입니다. 정렬할 때 전체 표를 함께 정렬하세요.'],
  ['미확인 정보', '공식 성취기준 코드, 학년, 교과서명, 판본은 미확인으로 시작합니다. 근거 자료로 확인한 내용만 입력하세요. 원문 단원·성취기준 표기로 학년이나 공식 코드를 추정하지 않습니다.'],
  ['검토 순서', '표 머리글의 필터로 출판사·단원·활동을 찾습니다. 교과서 또는 공식 자료의 정확한 판본과 해당 페이지를 확보한 뒤 원문 6열을 대조합니다.'],
  ['대조 근거', 'N열에 교과서명·판본·페이지 또는 공식 자료명·위치를 입력합니다. 확인할 수 있는 링크가 있으면 함께 기록하세요.'],
  ['수정 입력', '수정이 필요한 항목만 O:T 열에 입력합니다. 수정 셀이 비어 있으면 수정 제안이 없는 상태입니다. 값을 삭제해야 하면 검토 메모에 대상 열과 이유를 명시하세요.'],
  ['준비물 원문', '교구 원문은 쉼표로 자동 분리하지 않았습니다. 괄호 안 쉼표와 설명을 포함한 원문을 그대로 보존합니다. 교구 미기재 25행은 원문 빈 셀로 유지합니다.'],
  ['수량·안전 정보', '원문에 없는 수량·계산 기준·약품 위험성·폐기 방법은 추가하지 않습니다. 확인한 별도 근거가 있을 때 검토 메모에 자료명과 위치를 기록하세요.'],
  ['대조 상태', '교과서 대조 미확인: 아직 대조하지 않음. 대조 중: 일부 확인 진행. 수정 필요: 원문과 차이 발견. 대조 완료: 해당 행 원문 6열의 대조를 마침.'],
  ['완료 기록', '대조 완료 전에 교과서명·판본·대조 근거·검토자·검토일을 기록하고 수정 제안을 점검하세요. 공식 코드나 학년을 확인하지 못했다면 해당 셀의 미확인을 유지하세요.'],
  ['검토일', 'V열에는 실제 검토일을 Excel 날짜로 입력합니다. 표시 형식은 yyyy-mm-dd입니다.'],
  ['입력 구분', '회청색 A:H는 원문, 연노랑 I:W는 검토 입력입니다. 색상 외에도 열 제목으로 역할을 구분했습니다.'],
  ['사이트 반영', '검토표를 저장해도 사이트 데이터에는 자동 반영되지 않습니다. 검토 완료 후 id 기준으로 변경 내용을 별도 확인하여 데이터 파일에 반영해야 합니다.'],
  ['재생성 주의', '재생성은 최초 상태의 새 검토표를 만듭니다. 작성한 검토 내용은 이전 파일에만 있으므로 반드시 백업하세요. 기본 실행은 기존 검토표 덮어쓰기를 거부합니다.'],
  ['원본 JSON', 'science_experiment_supplies.json'],
  ['원본 Excel', source.metadata.source_file],
  ['원본 시트', source.metadata.primary_sheet],
  ['원본 Excel SHA-256', source.metadata.source_sha256],
  ['현재 JSON SHA-256', sha256],
];
guide.getRange('A2').values = [['검토 방법']];
guide.getRange('A4:B4').values = [['항목', '내용']];
guide.getRange(`A5:B${guideRows.length + 4}`).values = guideRows;
guide.getRange(`A1:B${guideRows.length + 4}`).format.font = { name: 'Malgun Gothic', size: 11, color: '#172B40' };
guide.getRange('A2').format.font = { name: 'Malgun Gothic', size: 15, bold: true };
guide.getRange('A2:B2').format.rowHeight = 28;
guide.getRange('A4:B4').format = { fill: '#304967', font: { name: 'Malgun Gothic', size: 11, color: '#FFFFFF', bold: true }, horizontalAlignment: 'center', verticalAlignment: 'center', rowHeight: 28 };
guide.getRange(`A5:B${guideRows.length + 4}`).format.verticalAlignment = 'top';
guide.getRange(`A5:B${guideRows.length + 4}`).format.wrapText = true;
guide.getRange(`A1:A${guideRows.length + 4}`).format.columnWidth = 27;
guide.getRange(`B1:B${guideRows.length + 4}`).format.columnWidth = 112;
guide.getRange(`A5:A${guideRows.length + 4}`).format.fill = '#F4F7FA';
for (let index = 0; index < guideRows.length; index++) {
  const lines = Math.ceil(guideRows[index][1].length / 56);
  guide.getRangeByIndexes(index + 4, 0, 1, 2).format.rowHeight = Math.max(32, lines * 18 + 14);
}
workbook.recalculate();

// Full data comparison is independent of presentation checks.
const actual = review.getRange(`A6:H${lastRow}`).values;
assert.equal(actual.length, source.data.length);
for (let index = 0; index < actual.length; index++) {
  for (let col = 0; col < originalKeys.length; col++) {
    const expected = source.data[index][originalKeys[col]];
    // Literal introducers may be represented internally with a leading quote.
    assert.ok(actual[index][col] === expected || actual[index][col] === literal(expected), `Source mismatch ${index + 1}/${originalKeys[col]}`);
  }
}
assert.equal(source.data.filter(row => row['교구'] === null).length, 25);
assert.ok(review.getRange(`M6:M${lastRow}`).values.every(([status]) => status === '교과서 대조 미확인'));
assert.ok(review.getRange(`I6:L${lastRow}`).values.every(row => row.every(value => value === '미확인')));
assert.ok(review.getRange(`N6:W${lastRow}`).values.every(row => row.every(value => value === null || value === '')));
for (const [name, range] of [['탐구활동 검토', 'A5:H7'], ['탐구활동 검토', 'I5:W7'], ['검토 방법', 'A4:B9']]) {
  const inspection = await workbook.inspect({ kind: 'table', range: `'${name}'!${range}`, include: 'values,formulas', tableMaxRows: 6, tableMaxCols: 15, tableMaxCellChars: 70, maxChars: 3500 });
  await fs.appendFile(path.join(outputDir, 'inspection.ndjson'), inspection.ndjson + '\n');
}
const errors = await workbook.inspect({ kind: 'match', searchTerm: '#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!', options: { useRegex: true, maxResults: 100 }, summary: 'Formula error scan' });
await fs.writeFile(path.join(outputDir, 'formula-scan.ndjson'), errors.ndjson);
for (const [file, sheetName, range] of (process.argv.includes('--skip-render') ? [] : [
  ['review-original.png', '탐구활동 검토', 'A2:H9'],
  ['review-inputs.png', '탐구활동 검토', 'I5:N9'],
  ['review-corrections.png', '탐구활동 검토', 'O5:W7'],
  ['review-guide.png', '검토 방법', 'A2:B16'],
  ['review-guide-continuation.png', '검토 방법', 'A17:B27'],
])) {
  const preview = await workbook.render({ sheetName, range, scale: 1, format: 'png' });
  await fs.writeFile(path.join(outputDir, file), new Uint8Array(await preview.arrayBuffer()));
}
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
assert.equal(crypto.createHash('sha256').update(await fs.readFile(sourcePath)).digest('hex'), sha256);
await fs.writeFile(path.join(outputDir, 'build-validation.json'), JSON.stringify({
  output: outputPath,
  sourceJsonSha256: sha256,
  records: source.data.length,
  preservedColumns: originalKeys,
  sourceCellsCompared: source.data.length * originalKeys.length,
  missingSuppliesPreserved: 25,
  unverifiedReviewRows: 454,
  inputFieldsUnfilled: true,
  sourceUnchanged: true,
  worksheetNames: ['탐구활동 검토', '검토 방법'],
  note: 'Rendered ranges and internal values checked. Saved XLSX is independently verified by verify-review.py.',
}, null, 2));
console.log(JSON.stringify({ outputPath, rows: source.data.length, sourceCellsCompared: source.data.length * originalKeys.length }));

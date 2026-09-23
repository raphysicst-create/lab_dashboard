import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { filterActivities, sanitizePreferences } from '../site/dist/core.js';
const root = new URL('../', import.meta.url);
const read = name => JSON.parse(readFileSync(new URL(name, root), 'utf8').replace(/^\uFEFF/, ''));
const source = read('outputs/extraction/combined-20260922/decision_history/20260923-integrated-science/science_experiment_supplies_combined.json');
const highSource = read('outputs/extraction/integrated-science-20260923/science_experiment_supplies_integrated_science.json');
const highInventory = read('outputs/extraction/integrated-science-20260923/achievement_mapping/standards_inventory.json');
const activities = read('site/dist/data/activities.json');
const achievements = read('site/dist/data/achievements.json');
const textbooks = read('site/dist/data/textbooks.json');
const research = read('outputs/research/achievement-standards-20260923/achievement_findings.json');
assert.equal(source.data.length, 862);
assert.equal(highSource.data.length, 415);
assert.equal(activities.length, 1277);
const activityById = new Map(activities.map(activity => [activity.id, activity]));
const middleActivities = activities.filter(activity => activity.school_level === '중학교');
const highActivities = activities.filter(activity => activity.school_level === '고등학교');
assert.equal(middleActivities.length, 862);
assert.equal(highActivities.length, 415);
assert.equal(new Set(activities.map(a => a.id)).size, activities.length);
const achievementIds = new Set(achievements.map(a => a.id));
const achievementById = new Map(achievements.map(a => [a.id, a]));
const officialByCode = new Map(research.official_standards.map(standard => [standard.code, standard]));
const researchByActivity = new Map(research.activity_mappings.map(mapping => [mapping.activity_id, mapping]));
const textbookIds = new Set(textbooks.map(a => a.id));
assert.equal(achievements.length, 118);
assert.equal(achievementIds.size, achievements.length);
assert.equal(officialByCode.size, 87);
assert.equal(researchByActivity.size, 408);
for (const row of source.data) {
  const activity = activityById.get(row.id);
  assert.ok(activity, row.id);
  for (const [original, output] of [['id','id'],['source_row','source_row'],['단원명','unit'],['성취기준','achievement_raw'],['출판사','publisher_raw'],['쪽','page'],['탐구활동','title'],['교구','materials_raw']]) assert.deepEqual(activity[output], row[original]);
  const book = source.metadata.source_datasets.flatMap(d => d.original_metadata.source_books ?? []).find(b => b.book_id === row.source?.book_id);
  const unitNumber = row['단원명'].match(/^(\d+)\./)?.[1];
  assert.equal(activity.unit_number, unitNumber == null ? null : Number(unitNumber));
  assert.equal(activity.grade, book ? book.grade : unitNumber <= 8 ? 1 : 2);
  assert.equal(activity.school_level, '중학교');
  assert.equal(activity.grade_key, String(activity.grade));
  assert.equal(activity.grade_label, `중${activity.grade}`);
  assert.deepEqual(activity.achievement_ids, activity.achievement_id ? [activity.achievement_id] : []);
  assert.deepEqual(activity.equipment, row['실험 기자재']);
  assert.deepEqual(activity.supplies, row['실험 준비물']);
  assert.ok(!activity.source && !activity['준비물 분류']);
  const finding = researchByActivity.get(activity.id);
  if (finding?.status === 'candidate' || finding?.status === 'unconfirmed') {
    assert.equal(activity.achievement_raw, null);
    assert.equal(activity.achievement_id, null);
  } else if (row['성취기준'] == null) {
    assert.equal(activity.achievement_id, null);
  } else {
    assert.ok(achievementIds.has(activity.achievement_id));
    const achievement = achievementById.get(activity.achievement_id);
    assert.ok(achievement.grades.includes(activity.grade));
    assert.equal(achievement.raw_text, activity.achievement_raw);
    if (finding) {
      assert.ok(['direct', 'scope_based'].includes(finding.status));
      assert.deepEqual(finding.standard_codes, [achievement.code]);
    } else {
      assert.equal(achievement.unit_number, activity.unit_number);
    }
  }
  assert.ok(textbookIds.has(activity.textbook_id));
  assert.ok(!JSON.stringify(activity).includes('textbook_not_checked'));
}
assert.deepEqual([...new Set(middleActivities.map(a => a.unit_number).filter(n => n != null))].sort((a, b) => a - b), Array.from({length: 15}, (_, i) => i + 1));
// Preserve all 87 existing public IDs, including standards without activity matches.
for (const standard of source.achievement_standards) {
  const serialized = `[${JSON.stringify(standard.unit)}, ${JSON.stringify(standard.display_text)}]`;
  const id = `ACH-${createHash('sha256').update(serialized).digest('hex').slice(0,16)}`;
  assert.equal(achievementById.get(id)?.code, standard.code);
  assert.equal(achievementById.get(id)?.raw_text, standard.display_text);
}
const highByCode = new Map(highInventory.standards.map(standard => [standard.code, standard]));
assert.equal(highByCode.size, 31);
assert.equal(achievements.filter(a => a.school_level === '고등학교').length, 31);
for (const achievement of achievements) {
  const [, unitNumber, sequence] = achievement.raw_text.match(/^(\d+)-(\d+)\./);
  assert.equal(achievement.unit_number, Number(unitNumber));
  assert.equal(achievement.sequence, Number(sequence));
  if (achievement.school_level === '고등학교') {
    const standard = highByCode.get(achievement.code);
    assert.ok(standard, achievement.code);
    const [,volume,unit,sequence] = achievement.code.match(/^10통과([12])-(\d{2})-(\d{2})$/);
    assert.equal(achievement.volume, Number(volume));
    assert.equal(achievement.unit_number, Number(unit));
    assert.equal(achievement.sequence, Number(sequence));
    assert.equal(achievement.sort_order, 100 + Number(volume)*10 + Number(unit));
    assert.equal(achievement.grade_key, 'high-1');
    assert.equal(achievement.raw_text, `${Number(unit)}-${Number(sequence)}. ${standard.text}`);
  } else {
    assert.ok(officialByCode.has(achievement.code));
  }
  assert.deepEqual(achievement.grades, [...new Set(activities.filter(a => a.achievement_ids.includes(achievement.id)).map(a => a.grade))].sort());
}
for (const row of highSource.data) {
  const activity = activityById.get(row.id);
  assert.ok(activity, row.id);
  for (const [original, output] of [['id','id'],['source_row','source_row'],['단원명','unit_raw'],['출판사','publisher_raw'],['쪽','page'],['탐구활동','title'],['교구','materials_raw']]) {
    assert.deepEqual(activity[output], row[original], `${row.id}: ${output}`);
  }
  assert.equal(activity.school_level, '고등학교');
  assert.equal(activity.grade, 1);
  assert.equal(activity.grade_key, 'high-1');
  assert.equal(activity.grade_label, '고1');
  assert.equal(activity.volume, Number(row.source.book_id.match(/IS([12])$/)[1]));
  assert.equal(activity.unit, `통합과학 ${activity.volume} · ${row['단원명']}`);
  const unitNumber = row['단원명'].match(/^\s*(\d+)\./)?.[1];
  assert.equal(activity.unit_number, unitNumber == null ? null : Number(unitNumber));
  assert.equal(activity.equipment, null);
  assert.equal(activity.supplies, null);
  assert.equal(activity.material_classification_pending, true);
  assert.deepEqual(activity.achievement_ids.map(id => achievementById.get(id)?.code), row['성취기준코드']);
  assert.equal(activity.achievement_id, activity.achievement_ids[0] ?? null);
  assert.equal(activity.achievement_raw, activity.achievement_ids.map(id => achievementById.get(id).raw_text).join('\n') || null);
  assert.ok(textbookIds.has(activity.textbook_id));
  assert.ok(!activity.source && !activity['준비물 분류']);
}
assert.equal(research.activity_mappings.filter(a => ['direct', 'scope_based'].includes(a.status)).length, 370);
assert.equal(research.activity_mappings.filter(a => ['candidate', 'unconfirmed'].includes(a.status)).length, 38);
assert.deepEqual(read('site/dist/data/quantities.json'), []);
assert.ok(read('site/dist/data/chemicals.json').length > 0);
assert.ok(read('site/dist/data/materials.json').length > 0);
assert.equal(middleActivities.filter(a => a.materials_raw == null).length, 103);
const publishers = [...new Set(activities.map(a => a.publisher_raw))];
const defaults = {grade:'all',unit:'all',achievement:'all',publishers,query:''};
assert.equal(filterActivities(activities, defaults).length, 1277);
assert.equal(filterActivities(activities, {...defaults,publishers:['비상']}).length, 111);
assert.equal(filterActivities(activities, {...defaults,publishers:[]}).length, 0);
assert.equal(filterActivities(activities, {...defaults,grade:'1'}).length, 328);
assert.equal(filterActivities(activities, {...defaults,grade:'2'}).length, 446);
assert.equal(filterActivities(activities, {...defaults,grade:'3'}).length, 88);
assert.deepEqual(filterActivities(activities, {...defaults,grade:'high-1'}), highActivities);
assert.equal(filterActivities(activities, {...defaults,grade:'unknown'}).length, 0);
for (const standard of achievements) {
  const expected = activities.filter(activity => activity.achievement_ids.includes(standard.id));
  assert.deepEqual(filterActivities(activities, {...defaults,achievement:standard.id}), expected);
  for (const grade of standard.grades) {
    assert.ok(filterActivities(activities, {...defaults,grade:standard.school_level === '고등학교' ? 'high-1' : String(grade),achievement:standard.id}).length > 0);
  }
}
const multiStandardActivities = highActivities.filter(activity => activity.achievement_ids.length > 1);
assert.ok(multiStandardActivities.length > 0);
for (const activity of multiStandardActivities) {
  for (const achievement of activity.achievement_ids.slice(1)) {
    assert.ok(filterActivities(activities, {...defaults,grade:'high-1',achievement}).includes(activity));
  }
}
for (const unit of new Set(highActivities.map(activity => activity.unit))) {
  assert.deepEqual(filterActivities(activities, {...defaults,grade:'high-1',unit}), highActivities.filter(activity => activity.unit === unit));
  assert.equal(filterActivities(activities, {...defaults,grade:'1',unit}).length, 0);
}
assert.equal(activities.reduce((n,a)=>n+(a.equipment?.length??0),0),2924);
assert.equal(activities.reduce((n,a)=>n+(a.supplies?.length??0),0),1095);
const unitEight = activities.find(a => a.unit_number === 8).unit;
const unitNine = activities.find(a => a.unit_number === 9).unit;
assert.equal(filterActivities(activities, {...defaults,grade:'1',unit:unitEight}).length, 45);
assert.equal(filterActivities(activities, {...defaults,grade:'2',unit:unitNine}).length, 44);
assert.equal(filterActivities(activities, {...defaults,grade:'1',unit:unitNine}).length, 0);
const chemicalResults = filterActivities(activities, {...defaults,query:'염산'});
assert.ok(chemicalResults.length > 0);
assert.ok(chemicalResults.every(a => [a.title,a.materials_raw,a.unit,a.achievement_raw].some(value => value?.includes('염산'))));
assert.deepEqual(filterActivities(activities, {...defaults,query:'전자저울'}),filterActivities(activities, {...defaults,query:'전자 저울'}));
const sanitized=sanitizePreferences({publishers:['비상','unknown','비상'],selected:['activity_0001','absent','activity_0001'],students:10,classes:2,groupSize:4},publishers);
assert.deepEqual(sanitized, {publishers:['비상'],publisherCatalog:publishers});
assert.deepEqual(sanitizePreferences({publishers:['동아','미래앤','비상','천재(임성숙)','천재(정대홍)']},publishers).publishers,publishers);
assert.equal(Object.hasOwn(sanitized,'selected'),false);



console.log(JSON.stringify({status:'passed',activityRows:activities.length,middleRows:middleActivities.length,highRows:highActivities.length,standards:achievements.length,multipleStandardRows:multiStandardActivities.length,sourceCellsCompared:middleActivities.length*8+highActivities.length*7,publishers:publishers.length,chemicalSearchResults:chemicalResults.length,source:fileURLToPath(root)},null,2));

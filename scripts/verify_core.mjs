import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { filterActivities, sanitizePreferences } from '../site/dist/core.js';
const root = new URL('../', import.meta.url);
const read = name => JSON.parse(readFileSync(new URL(name, root), 'utf8').replace(/^\uFEFF/, ''));
const publisherAliases = new Map([['동아','동아출판'],['미래앤','미래엔'],['비상','비상교육']]);
const canonicalPublisher = name => publisherAliases.get(name) ?? name;
const source = read('outputs/extraction/combined-20260922/decision_history/20260923-integrated-science/science_experiment_supplies_combined.json');
const highSource = read('outputs/extraction/integrated-science-20260923/science_experiment_supplies_integrated_science.json');
const removedActivityId = 'donga_IS2_045';
const retainedHighRows = highSource.data.filter(row => row.id !== removedActivityId);
const highInventory = read('outputs/extraction/integrated-science-20260923/achievement_mapping/standards_inventory.json');
const beforeUnits = read('outputs/extraction/combined-20260922/decision_history/20260923-units/science_experiment_supplies_combined.json');
const normalizedSource = read('outputs/extraction/combined-20260922/science_experiment_supplies_combined.json');
const activities = read('site/dist/data/activities.json');
const achievements = read('site/dist/data/achievements.json');
const textbooks = read('site/dist/data/textbooks.json');
const research = read('outputs/research/achievement-standards-20260923/achievement_findings.json');
assert.equal(source.data.length, 862);
assert.equal(highSource.data.length, 415);
assert.equal(activities.length, 1276);
assert.equal(normalizedSource.data.length,1276);
assert.equal(retainedHighRows.length,414);
const activityById = new Map(activities.map(activity => [activity.id, activity]));
const middleActivities = activities.filter(activity => activity.school_level === '중학교');
const highActivities = activities.filter(activity => activity.school_level === '고등학교');
assert.equal(middleActivities.length, 862);
assert.equal(highActivities.length, 414);
assert.equal(activityById.has(removedActivityId),false);
assert.equal(normalizedSource.data.some(row => row.id === removedActivityId),false);
assert.equal(activities.some(activity => activity.unit.includes('부록')),false);
assert.equal(new Set(activities.map(a => a.id)).size, activities.length);
const achievementIds = new Set(achievements.map(a => a.id));
const achievementById = new Map(achievements.map(a => [a.id, a]));
const officialByCode = new Map(research.official_standards.map(standard => [standard.code, standard]));
const researchByActivity = new Map(research.activity_mappings.map(mapping => [mapping.activity_id, mapping]));
const textbookIds = new Set(textbooks.map(a => a.id));
const normalizedById = new Map(normalizedSource.data.map(row => [row.id,row]));
const highClassificationFields = new Set(['실험 기자재','실험 준비물','분류 보류','준비물 분류','준비물 표시 방식','준비물 분류 비항목']);
const canonicalUnitKey = text => text.split(/[>/]/)[0].replace(/^통합과학\s*[12]\s*·\s*/, '').replace(/^[\dⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+\.\s*/, '').replace(/[\s·⋅]/g,'');
assert.equal(beforeUnits.data.length,1277);
assert.deepEqual(normalizedSource.achievement_standards,beforeUnits.achievement_standards);
const unitIds = new Map();
for (const row of beforeUnits.data) {
  if (row.id === removedActivityId) {
    assert.equal(row['단원명'],'부록');
    assert.equal(normalizedById.has(row.id),false);
    continue;
  }
  const normalized = normalizedById.get(row.id);
  const activity = activityById.get(row.id);
  assert.ok(normalized && activity,row.id);
  for (const [field,value] of Object.entries(row)) {
    const classificationChanged = row['학교급'] === '고등학교' && highClassificationFields.has(field);
    if (field !== '단원명' && !classificationChanged) {
      assert.deepEqual(normalized[field],field === '출판사' ? canonicalPublisher(value) : value,`${row.id}: preserved ${field}`);
    }
  }
  assert.equal(normalized['출판사'],canonicalPublisher(row['출판사']));
  if (publisherAliases.has(row['출판사'])) assert.equal(normalized['출판사 원문'],row['출판사']);
  else assert.equal(Object.hasOwn(normalized,'출판사 원문'),false,`${row.id}: unchanged publisher needs no alias field`);
  assert.equal(activity.publisher_raw,canonicalPublisher(row['출판사']));
  assert.equal(activity.textbook_id,`TXT-${createHash('sha256').update(activity.publisher_raw).digest('hex').slice(0,16)}`);
  assert.equal(normalized['단원명 원문'],row['단원명']);
  assert.equal(activity.unit_raw,row['단원명']);
  assert.equal(activity.unit,normalized['단원명']);
  assert.equal(activity.unit_number,normalized['단원 번호']);
  assert.ok(typeof normalized['단원 ID'] === 'string' && normalized['단원 ID'].length > 0);
  const high = activity.school_level === '고등학교';
  const originalMajorUnit = canonicalUnitKey(row['단원명']);
  assert.notEqual(originalMajorUnit,'부록');
  {
    const expectedStandard = achievements.find(standard =>
      (standard.school_level === '고등학교') === high && (!high || standard.volume === activity.volume)
      && canonicalUnitKey(standard.unit) === originalMajorUnit);
    assert.ok(expectedStandard,`${row.id}: original major unit ${row['단원명']}`);
    assert.equal(activity.unit,expectedStandard.unit);
    assert.equal(activity.unit_number,expectedStandard.unit_number);
  }
  if (unitIds.has(activity.unit)) assert.equal(normalized['단원 ID'],unitIds.get(activity.unit));
  unitIds.set(activity.unit,normalized['단원 ID']);
}
assert.equal(unitIds.size,29); // 23 middle units and six integrated-science units.
assert.equal(new Set(unitIds.values()).size,29);
assert.equal([...unitIds.values()].includes('high-2-appendix'),false);
assert.equal(achievements.length, 118);
assert.equal(achievementIds.size, achievements.length);
assert.equal(officialByCode.size, 87);
assert.equal(researchByActivity.size, 408);
for (const row of source.data) {
  const activity = activityById.get(row.id);
  assert.ok(activity, row.id);
  for (const [original, output] of [['id','id'],['source_row','source_row'],['단원명','unit_raw'],['성취기준','achievement_raw'],['출판사','publisher_raw'],['쪽','page'],['탐구활동','title'],['교구','materials_raw']]) {
    assert.deepEqual(activity[output],original === '출판사' ? canonicalPublisher(row[original]) : row[original]);
  }
  const book = source.metadata.source_datasets.flatMap(d => d.original_metadata.source_books ?? []).find(b => b.book_id === row.source?.book_id);
  const unitNumber = row['단원명'].match(/^(\d+)\./)?.[1];
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
assert.deepEqual([...new Set(middleActivities.map(a => a.unit_number))].sort((a, b) => a - b), Array.from({length: 23}, (_, i) => i + 1));
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
for (const row of retainedHighRows) {
  const activity = activityById.get(row.id);
  assert.ok(activity, row.id);
  for (const [original, output] of [['id','id'],['source_row','source_row'],['단원명','unit_raw'],['출판사','publisher_raw'],['쪽','page'],['탐구활동','title'],['교구','materials_raw']]) {
    assert.deepEqual(activity[output], original === '출판사' ? canonicalPublisher(row[original]) : row[original], `${row.id}: ${output}`);
  }
  assert.equal(activity.school_level, '고등학교');
  assert.equal(activity.grade, 1);
  assert.equal(activity.grade_key, 'high-1');
  assert.equal(activity.grade_label, '고1');
  assert.equal(activity.volume, Number(row.source.book_id.match(/IS([12])$/)[1]));
  const classified = normalizedById.get(row.id);
  assert.deepEqual(activity.equipment, classified['실험 기자재'],`${row.id}: equipment`);
  assert.deepEqual(activity.supplies, classified['실험 준비물'],`${row.id}: supplies`);
  if (row['교구'] == null) {
    assert.equal(activity.equipment,null);
    assert.equal(activity.supplies,null);
  } else {
    assert.ok(Array.isArray(activity.equipment),`${row.id}: equipment array`);
    assert.ok(Array.isArray(activity.supplies),`${row.id}: supplies array`);
    for (const item of [...activity.equipment,...activity.supplies]) {
      assert.ok(typeof item === 'string' && item.trim().length > 0);
      assert.ok(row['교구'].includes(item),`${row.id}: category item preserves source text`);
    }
    assert.deepEqual(classified['분류 보류'],[],`${row.id}: no pending category`);
  }
  assert.equal(activity.material_classification_pending, false);
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
assert.equal(activities.filter(a => a.materials_raw == null).length,279);
assert.equal(activities.filter(a => a.achievement_id == null).length,41);
assert.equal(highActivities.filter(a => a.achievement_id == null).length,3);
const publishers = [...new Set(activities.map(a => a.publisher_raw))];
const expectedPublishers = ['동아출판','미래엔','비상교육','천재(임성숙)','천재(정대홍)','천재교과서','지학사','YBM'];
assert.deepEqual([...publishers].sort(),[...expectedPublishers].sort());
assert.equal(textbooks.length,8);
assert.deepEqual(textbooks.map(book => book.publisher_raw).sort(),[...expectedPublishers].sort());
for (const book of textbooks) assert.equal(book.id,`TXT-${createHash('sha256').update(book.publisher_raw).digest('hex').slice(0,16)}`);
const defaults = {grade:'all',unit:'all',achievement:'all',publishers,query:''};
assert.equal(filterActivities(activities, defaults).length, 1276);
assert.equal(filterActivities(activities, {...defaults,publishers:['비상교육']}).length, 209);
assert.equal(filterActivities(activities, {...defaults,publishers:['비상교육'],grade:'high-1'}).length,98);
assert.equal(filterActivities(middleActivities, {...defaults,publishers:['비상교육']}).length,111);
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
for (const [grade,unitCount] of [['1',8],['2',8],['3',8],['high-1',6]]) {
  const gradeActivities = activities.filter(activity => activity.grade_key === grade);
  const units = new Set(gradeActivities.map(activity => activity.unit));
  assert.equal(units.size,unitCount);
  let filteredCount = 0;
  for (const unit of units) {
    const expected = gradeActivities.filter(activity => activity.unit === unit);
    const actual = filterActivities(activities, {...defaults,grade,unit});
    assert.deepEqual(actual,expected);
    filteredCount += actual.length;
  }
  assert.equal(filteredCount,gradeActivities.length);
}
assert.equal(middleActivities.reduce((n,a)=>n+(a.equipment?.length??0),0),2924);
assert.equal(middleActivities.reduce((n,a)=>n+(a.supplies?.length??0),0),1095);
assert.ok(highActivities.some(a => a.equipment?.length && a.supplies?.length));
assert.ok(highActivities.some(a => a.materials_raw != null && a.supplies?.length === 0));
const unitEight = activities.find(a => a.unit_number === 8).unit;
const unitNine = activities.find(a => a.unit_number === 9).unit;
assert.equal(filterActivities(activities, {...defaults,grade:'1',unit:unitEight}).length, 45);
assert.equal(filterActivities(activities, {...defaults,grade:'2',unit:unitNine}).length, 67);
assert.equal(filterActivities(activities, {...defaults,grade:'1',unit:unitNine}).length, 0);
const unitOne = middleActivities.find(a => a.unit_number === 1).unit;
const firstUnitActivities = filterActivities(activities,{...defaults,grade:'1',unit:unitOne});
assert.equal(firstUnitActivities.length,23);
assert.ok(firstUnitActivities.some(a => a.publisher_raw === '지학사'));
assert.ok(firstUnitActivities.some(a => a.publisher_raw === 'YBM'));
assert.ok(new Set(firstUnitActivities.map(a => a.publisher_raw)).size > 2);
assert.equal(highActivities.filter(a => a.unit_number == null).length,0);
const chemicalResults = filterActivities(activities, {...defaults,query:'염산'});
assert.ok(chemicalResults.length > 0);
assert.ok(chemicalResults.every(a => [a.title,a.materials_raw,a.unit,a.achievement_raw].some(value => value?.includes('염산'))));
assert.deepEqual(filterActivities(activities, {...defaults,query:'전자저울'}),filterActivities(activities, {...defaults,query:'전자 저울'}));
const sanitized=sanitizePreferences({publishers:['비상','unknown','비상'],selected:['activity_0001','absent','activity_0001'],students:10,classes:2,groupSize:4},publishers);
assert.deepEqual(sanitized, {publishers:['비상교육'],publisherCatalog:publishers});
assert.deepEqual(sanitizePreferences({publishers:['동아','미래앤','비상','천재(임성숙)','천재(정대홍)']},publishers).publishers,publishers);
const legacyPublishers = ['동아','미래앤','비상','천재(임성숙)','천재(정대홍)','지학사','YBM','동아출판','미래엔','비상교육','천재교과서'];
assert.deepEqual(sanitizePreferences({publishers:['비상'],publisherCatalog:legacyPublishers},publishers).publishers,['비상교육']);
for (const selected of [['동아'],['동아출판'],['동아','동아출판']]) {
  assert.deepEqual(sanitizePreferences({publishers:selected,publisherCatalog:legacyPublishers},publishers).publishers,['동아출판']);
}
for (const selected of [['동아'],['동아출판']]) {
  assert.deepEqual(sanitizePreferences({publishers:selected,publisherCatalog:['동아','동아출판']},publishers).publishers,['동아출판']);
}
assert.deepEqual(sanitizePreferences({publishers:legacyPublishers,publisherCatalog:legacyPublishers},publishers).publishers,publishers);
assert.deepEqual(sanitizePreferences({publishers:[],publisherCatalog:legacyPublishers},publishers).publishers,[]);
assert.deepEqual(sanitizePreferences({publishers:['천재(임성숙)','천재(정대홍)','천재교과서'],publisherCatalog:legacyPublishers},publishers).publishers,['천재(임성숙)','천재(정대홍)','천재교과서']);
assert.equal(Object.hasOwn(sanitized,'selected'),false);



console.log(JSON.stringify({status:'passed',activityRows:activities.length,middleRows:middleActivities.length,highRows:highActivities.length,canonicalUnits:unitIds.size,unitRowsCompared:beforeUnits.data.length-1,excludedActivityId:removedActivityId,standards:achievements.length,multipleStandardRows:multiStandardActivities.length,sourceCellsCompared:middleActivities.length*8+highActivities.length*7,publishers:publishers.length,chemicalSearchResults:chemicalResults.length,source:fileURLToPath(root)},null,2));

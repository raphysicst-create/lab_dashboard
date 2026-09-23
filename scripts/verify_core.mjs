import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { filterActivities, sanitizePreferences } from '../site/dist/core.js';
const root = new URL('../', import.meta.url);
const read = name => JSON.parse(readFileSync(new URL(name, root), 'utf8').replace(/^\uFEFF/, ''));
const source = read('outputs/extraction/combined-20260922/science_experiment_supplies_combined.json');
const activities = read('site/dist/data/activities.json');
const achievements = read('site/dist/data/achievements.json');
const textbooks = read('site/dist/data/textbooks.json');
assert.equal(activities.length, source.data.length);
assert.equal(new Set(activities.map(a => a.id)).size, activities.length);
const achievementIds = new Set(achievements.map(a => a.id));
const achievementById = new Map(achievements.map(a => [a.id, a]));
const textbookIds = new Set(textbooks.map(a => a.id));
for (const [i, row] of source.data.entries()) {
  const activity = activities[i];
  for (const [original, output] of [['id','id'],['source_row','source_row'],['단원명','unit'],['성취기준','achievement_raw'],['출판사','publisher_raw'],['쪽','page'],['탐구활동','title'],['교구','materials_raw']]) assert.deepEqual(activity[output], row[original]);
  const book = source.metadata.source_datasets.flatMap(d => d.original_metadata.source_books ?? []).find(b => b.book_id === row.source?.book_id);
  const unitNumber = row['단원명'].match(/^(\d+)\./)?.[1];
  assert.equal(activity.unit_number, unitNumber == null ? null : Number(unitNumber));
  assert.equal(activity.grade, book ? book.grade : unitNumber <= 8 ? 1 : 2);
  assert.deepEqual(activity.equipment, row['실험 기자재']);
  assert.deepEqual(activity.supplies, row['실험 준비물']);
  assert.ok(!activity.source && !activity['준비물 분류']);
  if (row['성취기준'] == null) {
    assert.equal(activity.achievement_id, null);
  } else {
  assert.ok(achievementIds.has(activity.achievement_id));
  const achievement = achievementById.get(activity.achievement_id);
  assert.equal(achievement.unit_number, activity.unit_number);
  assert.equal(achievement.grade, activity.grade);
  assert.equal(achievement.raw_text, activity.achievement_raw);
  }
  assert.ok(textbookIds.has(activity.textbook_id));
  assert.ok(!JSON.stringify(activity).includes('textbook_not_checked'));
}
assert.deepEqual([...new Set(activities.map(a => a.unit_number).filter(n => n != null))].sort((a, b) => a - b), Array.from({length: 15}, (_, i) => i + 1));
for (const achievement of achievements) {
  const [, unitNumber, sequence] = achievement.raw_text.match(/^(\d+)-(\d+)\./);
  assert.equal(achievement.unit_number, Number(unitNumber));
  assert.equal(achievement.sequence, Number(sequence));
  assert.equal(achievement.grade, Number(unitNumber) <= 8 ? 1 : 2);
  assert.equal(achievement.code, null);
}
assert.equal(achievements.filter(a => a.grade === 1).length, 27);
assert.equal(achievements.filter(a => a.grade === 2).length, 29);
assert.deepEqual(read('site/dist/data/quantities.json'), []);
assert.ok(read('site/dist/data/chemicals.json').length > 0);
assert.ok(read('site/dist/data/materials.json').length > 0);
assert.equal(activities.filter(a => a.materials_raw == null).length, 103);
const publishers = [...new Set(activities.map(a => a.publisher_raw))];
const defaults = {grade:'all',unit:'all',achievement:'all',publishers,query:''};
assert.equal(filterActivities(activities, defaults).length, 862);
assert.equal(filterActivities(activities, {...defaults,publishers:['비상']}).length, 111);
assert.equal(filterActivities(activities, {...defaults,publishers:[]}).length, 0);
assert.equal(filterActivities(activities, {...defaults,grade:'1'}).length, 328);
assert.equal(filterActivities(activities, {...defaults,grade:'2'}).length, 446);
assert.equal(filterActivities(activities, {...defaults,grade:'3'}).length, 88);
assert.equal(filterActivities(activities, {...defaults,grade:'unknown'}).length, 0);
assert.equal(activities.reduce((n,a)=>n+(a.equipment?.length??0),0),2924);
assert.equal(activities.reduce((n,a)=>n+(a.supplies?.length??0),0),1095);
const unitEight = activities.find(a => a.unit_number === 8).unit;
const unitNine = activities.find(a => a.unit_number === 9).unit;
assert.equal(filterActivities(activities, {...defaults,grade:'1',unit:unitEight}).length, 45);
assert.equal(filterActivities(activities, {...defaults,grade:'2',unit:unitNine}).length, 44);
assert.equal(filterActivities(activities, {...defaults,grade:'1',unit:unitNine}).length, 0);
const chemicalResults = filterActivities(activities, {...defaults,query:'염산'});
assert.ok(chemicalResults.length > 0);
assert.ok(chemicalResults.every(a => a.materials_raw.includes('염산')));
assert.deepEqual(filterActivities(activities, {...defaults,query:'전자저울'}),filterActivities(activities, {...defaults,query:'전자 저울'}));
const sanitized=sanitizePreferences({publishers:['비상','unknown','비상'],selected:['activity_0001','absent','activity_0001'],students:10,classes:2,groupSize:4},publishers);
assert.deepEqual(sanitized, {publishers:['비상'],publisherCatalog:publishers});
assert.deepEqual(sanitizePreferences({publishers:['동아','미래앤','비상','천재(임성숙)','천재(정대홍)']},publishers).publishers,publishers);
assert.equal(Object.hasOwn(sanitized,'selected'),false);



console.log(JSON.stringify({status:'passed',activityRows:activities.length,sourceCellsCompared:activities.length*8,publishers:publishers.length,chemicalSearchResults:chemicalResults.length,source:fileURLToPath(root)},null,2));

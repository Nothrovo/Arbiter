import test from 'node:test';
import assert from 'node:assert/strict';
import {queryFrom,scopeParams} from '../../app/static/js/state/scope.js';
test('explicit empty selections fail closed and pagination is finite integer',()=>{
 assert.throws(()=>scopeParams({tenant:'Lab'},{ids:[]}),/pilihan|valid/i);
 assert.throws(()=>scopeParams({tenant:'Lab'},{ids:[true]}),/pilihan|valid/i);
 const q=queryFrom(new URLSearchParams('limit=Infinity&offset=Infinity'));
 assert.ok(Number.isInteger(q.offset)&&Number.isFinite(q.offset));
 assert.equal(queryFrom(new URLSearchParams('offset=1.5')).offset,1);
});

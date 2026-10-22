"""Regression tests with synthetic in-memory records only; never real SGU data."""
import json
import unittest
from typing import Any
from tests.test_ui_api import UIAPIContractTests, GROUP

class SafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        UIAPIContractTests.setUpClass.__func__(cls)
    def setUp(self):
        UIAPIContractTests.setUp(self)  # type: ignore[arg-type]
        self.db.connection.create_function('now', 0, lambda: '2026-01-01T12:00:00Z')
    tearDown = UIAPIContractTests.tearDown
    db: Any
    client: Any
    api: Any

    def test_summary_never_carries_log_sentinel_in_nested_parsed_details(self):
        sentinel = 'SYNTHETIC-PRIMARY-LOG-SENTINEL'
        self.db.connection.execute('UPDATE wazuh.alerts SET parsed_details = ? WHERE id = 1', (json.dumps({'message':sentinel,'details':{'log':sentinel}}),))
        response = self.client.get('/api/alerts?summary=true&tenant=Alpha')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(sentinel, response.text)
        self.assertNotIn('parsed_details', response.json()['items'][0])
        detail = self.client.get('/api/alerts/1?tenant=Alpha')
        self.assertIn(sentinel, detail.text)
        query = next(sql for sql,_ in self.db.calls if 'LIMIT' in sql and 'FROM wazuh.alerts' in sql)
        projection = query.split('FROM wazuh.alerts')[0]
        for heavy in ('a.raw', 'a.data', 'a.duplicate_instances', 'a.parsed_details'):
            self.assertNotIn(heavy, projection)

    def test_selected_export_is_all_or_nothing_with_missing_or_wrong_tenant_ids(self):
        for ids in ('1,999', '1,2'):
            response = self.client.get('/api/export/preview', params={'tenant':'Alpha','alert_ids':ids})
            self.assertEqual(response.status_code, 409, response.text[:160])

    def test_batch_review_rejects_entire_selection_before_update(self):
        response = self.client.post('/api/alerts/batch-review?tenant=Alpha', json={'alert_ids':[1,2], 'is_reviewed':True})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(any('UPDATE wazuh.alerts' in sql for sql,_ in self.db.calls))
        response = self.client.post('/api/alerts/batch-review?tenant=Alpha', json={'alert_ids':[1], 'is_reviewed':True})
        self.assertEqual(response.status_code,200,response.text)
        self.assertTrue(self.client.get('/api/alerts/1?tenant=Alpha').json()['is_reviewed'])

    def test_malformed_group_mutations_fail_before_queries(self):
        for method,path,body in [('put','/api/groups/no-uuid',{'title':'Synthetic'}),('delete','/api/groups/no-uuid',None),('post','/api/groups/no-uuid/members',{'alert_pks':[1]}),('delete','/api/groups/no-uuid/members/1',None)]:
            response = getattr(self.client,method)(path,**({'json':body} if body else {}))
            self.assertEqual(response.status_code,422,response.text[:100])
        self.assertEqual(self.db.calls,[])

    def test_scoped_empty_case_is_rejected_before_insert_with_clear_recovery(self):
        response=self.client.post('/api/groups?tenant=Alpha',json={'title':'Synthetic empty','alert_pks':[]})
        self.assertEqual(response.status_code,400,response.text)
        self.assertFalse(any('INSERT' in sql for sql,_ in self.db.calls))
        self.assertIn('bukti',response.json()['detail'].lower())

    def test_all_tenant_membership_validates_existence(self):
        response=self.client.post(f'/api/groups/{GROUP}/members',json={'alert_pks':[999]})
        self.assertEqual(response.status_code,400,response.text)

    def test_scoped_case_cannot_lose_its_last_visible_evidence(self):
        response=self.client.delete(f'/api/groups/{GROUP}/members/1?tenant=Alpha')
        self.assertEqual(response.status_code,409,response.text)
        self.assertEqual(self.client.get(f'/api/groups/{GROUP}?tenant=Alpha').status_code,200)

    def test_scoped_mutations_reject_invisible_case_and_empty_title(self):
        for method in ('put','delete'):
            url=f'/api/groups/{GROUP}?tenant=Gamma'
            response=getattr(self.client,method)(url,**({'json':{'title':'Synthetic'}} if method=='put' else {}))
            self.assertEqual(response.status_code,404,response.text)
        response=self.client.put(f'/api/groups/{GROUP}?tenant=Alpha',json={'title':'   '})
        self.assertEqual(response.status_code,400,response.text)

    def test_unicode_docx_filename_is_valid_http_header(self):
        self.db.connection.execute('UPDATE wazuh.analysis_groups SET title = ? WHERE id = ?',('Synthetic 日本語 investigation',GROUP))
        response=self.client.get('/api/export/docx',params={'group_id':GROUP,'tenant':'Alpha'})
        self.assertEqual(response.status_code,200)
        self.assertIn('filename*=',response.headers['Content-Disposition'])

if __name__=='__main__':
    unittest.main()

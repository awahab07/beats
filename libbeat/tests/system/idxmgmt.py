import datetime
import unittest
import pytest
from elasticsearch import NotFoundError


class IdxMgmt(unittest.TestCase):

    def __init__(self, client, index):
        self._client = client
        self._index = index if index != '' and index != '*' else 'mockbeat'

    def needs_init(self, s):
        return s == '' or s == '*'

    def delete(self, indices=[], policies=[]):
        indices = list([x for x in indices if x != ''])
        if not indices:
            indices == [self._index]
        for i in indices:
            self.delete_index_and_alias(i)
            self.delete_template(template=i)
        for i in [x for x in policies if x != '']:
            self.delete_policy(i)

    def delete_index_and_alias(self, index=""):
        if self.needs_init(index):
            index = self._index

        try:
            self._client.transport.perform_request('DELETE', "/" + index + "*")
        except NotFoundError:
            pass

    def delete_template(self, template=""):
        if self.needs_init(template):
            template = self._index

        try:
            self._client.transport.perform_request('DELETE', "/_template/" + template + "*")
        except NotFoundError:
            pass

    def delete_policy(self, policy):
        # Delete any existing policy starting with given policy
        policies = self._client.transport.perform_request('GET', "/_ilm/policy")
        for p, _ in policies.items():
            if not p.startswith(policy):
                continue
            try:
                self._client.transport.perform_request('DELETE', "/_ilm/policy/" + p)
            except NotFoundError:
                pass

    def assert_index_template_not_loaded(self, template):
        with pytest.raises(NotFoundError):
            self._client.transport.perform_request('GET', '/_template/' + template)

    def assert_legacy_index_template_loaded(self, template):
        resp = self._client.transport.perform_request('GET', '/_template/' + template)
        assert template in resp
        assert "lifecycle" not in resp[template]["settings"]["index"]

    def assert_index_template_loaded(self, template):
        resp = self._client.transport.perform_request('GET', '/_index_template/' + template)
        found = False
        for index_template in resp['index_templates']:
            if index_template['name'] == template:
                found = True
        assert found

    def assert_component_template_loaded(self, template):
        resp = self._client.transport.perform_request('GET', '/_component_template/' + template)
        found = False
        print(resp)
        for index_template in resp['component_templates']:
            if index_template['name'] == template:
                found = True
        assert found

    def assert_ilm_template_loaded(self, template, policy, alias):
        resp = self._client.transport.perform_request('GET', '/_template/' + template)
        assert resp[template]["settings"]["index"]["lifecycle"]["name"] == policy
        assert resp[template]["settings"]["index"]["lifecycle"]["rollover_alias"] == alias

    def assert_index_template_index_pattern(self, template, index_pattern):
        resp = self._client.transport.perform_request('GET', '/_template/' + template)
        assert template in resp
        assert resp[template]["index_patterns"] == index_pattern

    def assert_alias_not_created(self, alias):
        resp = self._client.transport.perform_request('GET', '/_alias')
        for name, entry in resp.items():
            if alias not in name:
                continue
            assert entry["aliases"] == {}, entry["aliases"]

    def assert_alias_created(self, alias, pattern=None):
        if pattern is None:
            pattern = self.default_pattern()
        name = alias + "-" + pattern
        resp = self._client.transport.perform_request('GET', '/_alias/' + alias)
        assert name in resp
        assert resp[name]["aliases"][alias]["is_write_index"] == True

    def assert_policy_not_created(self, policy):
        with pytest.raises(NotFoundError):
            self._client.transport.perform_request('GET', '/_ilm/policy/' + policy)

    def assert_policy_created(self, policy):
        resp = self._client.transport.perform_request('GET', '/_ilm/policy/' + policy)
        assert policy in resp
        assert resp[policy]["policy"]["phases"]["hot"]["actions"]["rollover"]["max_size"] == "50gb"
        assert resp[policy]["policy"]["phases"]["hot"]["actions"]["rollover"]["max_age"] == "30d"

    def assert_docs_written_to_alias(self, alias, pattern=None):
        # Refresh the indices to guarantee all documents are available
        # through the _search API.
        self._client.transport.perform_request('POST', '/_refresh')

        if pattern is None:
            pattern = self.default_pattern()
        name = alias + "-" + pattern
        data = self._client.transport.perform_request('GET', '/' + name + '/_search')
        self.assertGreater(data["hits"]["total"]["value"], 0)

    def default_pattern(self):
        d = datetime.datetime.now().strftime("%Y.%m.%d")
        return d + "-000001"

    def index_for(self, alias, pattern=None):
        if pattern is None:
            pattern = self.default_pattern()
        return "{}-{}".format(alias, pattern)

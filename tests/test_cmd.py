from collections import namedtuple
import pytest

from autopwn import Menus, _main
import subprocess

target_contents = '''
targets:
   - name: test
     ip_address: 127.0.0.1'''

@pytest.yield_fixture()
def target(tmpdir):
    test_target = tmpdir.join('target')
    test_target.write(target_contents)
    yield test_target

FakePopen = namedtuple('FakePopen', 'communicate')

def test_cmd(monkeypatch, target):
    monkeypatch.setitem(__builtins__, 'input', lambda _: 'y')

    def select_nmap(self, menu_items):
        self.item_selected = 4
    monkeypatch.setattr(Menus, 'display_assessment_menu', select_nmap)

    def fake(*args):
        assert args[0] == '/usr/bin/nmap -A -sS -sC -sV 127.0.0.1 -oA 20150420_autopwn_127.0.0.1_test/20150420_170645+0100_test_nmap_common_ports_127.0.0.1'
        return FakePopen(lambda : ('', ''))
    monkeypatch.setattr(subprocess, 'Popen', fake)

    _main(['-t', str(target), '-ir'])




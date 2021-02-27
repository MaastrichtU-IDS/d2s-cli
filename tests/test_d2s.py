from click.testing import CliRunner
import d2s.__main__ as d2s
import os.path

def test_d2s():
   runner = CliRunner()
   result = runner.invoke(d2s.init, [], input='\n')
   assert not result.exception
   assert os.path.isfile('README.md')
#    assert result.output == 'Foo: wau wau\nfoo=wau wau\n'
from click.testing import CliRunner
import d2s.__main__ as d2s
import os.path

def test_d2s():
   runner = CliRunner()
   result_init = runner.invoke(d2s.init, [], input='\n')
   assert not result_init.exception
   # assert os.path.isfile('README.md')
   result_dataset = runner.invoke(d2s.new.dataset, [], input='\n')
#    assert result.output == 'Foo: wau wau\nfoo=wau wau\n'
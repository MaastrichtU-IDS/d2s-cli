from click.testing import CliRunner
import d2s 
import os.path

def test_d2s():
   runner = CliRunner()
   result = runner.invoke(d2s.init, ['d2s-test-project'], input='\n\n')
   assert not result.exception
   assert os.path.isfile('d2s-cwl-workflows/docker-compose.yaml')
#    assert result.output == 'Foo: wau wau\nfoo=wau wau\n'
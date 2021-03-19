from click.testing import CliRunner
import d2s.__main__ as d2s
import d2s.generate_metadata as generate_metadata
import os.path

def test_d2s_init():
   runner = CliRunner()
   result_init = runner.invoke(d2s.init, [], input='\n')
   assert not result_init.exception
   # assert os.path.isfile('README.md')
   # result_dataset = runner.invoke(d2s.new.dataset, [], input='\n')
#    assert result.output == 'Foo: wau wau\nfoo=wau wau\n'

def test_generate_metadata():
   sparql_endpoint_url = 'https://graphdb.dumontierlab.com/repositories/umids-kg'
   output_metadata = generate_metadata.generate_hcls_from_sparql(sparql_endpoint_url, sparql_endpoint_url, 'hcls', None)
   assert len(output_metadata) > 10
import json,pytest
from config import Config,ConfigError,load_config

def test_defaults_and_cross_midnight():
 c=Config().validate();assert c.enabled and c.quiet_start=='22:30' and c.quiet_end=='07:00' and c.required_barks==5
def test_unknown_rejected():
 with pytest.raises(ConfigError,match='unknown'):Config.from_dict({'surprise':1})
def test_malformed_and_unsafe(tmp_path):
 p=tmp_path/'x.json';p.write_text('{bad')
 with pytest.raises(ConfigError,match='invalid JSON'):load_config(p)
 with pytest.raises(ConfigError,match='inside'):Config.from_dict({'response_path':'../secret.wav'},tmp_path)
 with pytest.raises(ConfigError,match='lower'):Config.from_dict({'bark_on_threshold':.2,'bark_off_threshold':.3})

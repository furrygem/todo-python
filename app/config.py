from dataclasses import dataclass
from yamldataclassconfig import YamlDataClassConfig


class Config:
    @dataclass
    class ConfigData(YamlDataClassConfig):
        jwt_encode_key_file: str | None = None
        jwt_decode_key_file: str | None = None
        jwt_encode_key: str | None = None
        jwt_decode_key: str | None = None
        jwt_algorithm: str | None = None
        jwt_accept_algorithms: list[str] | None = None

        database_url: str | None = None

    def __init__(self, yaml_config_file: str):
        # yaml.load(config_f, self.ConfigData)
        self.config = self.ConfigData()
        self.config.load(yaml_config_file)
        if not self.config.jwt_encode_key and self.config.jwt_encode_key_file:
            with open(self.config.jwt_encode_key_file) as jwt_encode_key_fd:
                key = jwt_encode_key_fd.read()
                key.strip('\n')
                self.config.jwt_encode_key = key

        if not self.config.jwt_decode_key and self.config.jwt_decode_key_file:
            with open(self.config.jwt_decode_key_file) as jwt_decode_key_fd:
                key = jwt_decode_key_fd.read()
                key.strip('\n')
                self.config.jwt_decode_key = key

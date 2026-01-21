import os
from prance import ResolvingParser
from pathlib import Path

dir_path = Path(os.path.abspath(__file__)).parent
spec_path = os.path.join(dir_path.parent, "openapi", "openapi.yaml")

parser = ResolvingParser(spec_path)

RecommendationSchema = parser.specification['components']['schemas']['RecommendationObject']
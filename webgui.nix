{
  mkYarnPackage,
  fetchYarnDeps,
  fetchFromGitHub,
}:
mkYarnPackage rec {
  name = "CERBSim";
  version = "0.2.14-unstable-2024-10-14";

  src = fetchFromGitHub {
    owner = "CERBSim";
    repo = "webgui";
    rev = "52ceac6c23717c6b17026da4e7b86790ebd3b5a8";
    hash = "sha256-WRxkAml/ReoQ4HJyvDmzGn7zC+PGGjo9UVlz70PbKAc=";
  };

  # packageJSON = ./package.json;

  offlineCache = fetchYarnDeps {
    yarnLock = "${src}/yarn.lock";
    hash = "sha256-dW5zbNOpawF64LAaHly02Xgsa8C4seFIXBJLwd8BTVo=";
  };

  # distPhase = "true";

  buildPhase = ''
    yarn --offline build
  '';
}

{
  buildPythonPackage,
  fetchFromGitHub,
  lib,
  jupyter-packaging,
  jupyterlab,
  jupyter,
  setuptools,
  packaging,
  yarnConfigHook,
  fetchYarnDeps,
  nodejs,
  numpy,
  jupyterlab-widgets,
  ipywidgets,
}:

buildPythonPackage rec {
  pname = "webgui_jupyter_widgets";
  version = "0.2.31";
  pyproject = true;

  src = fetchFromGitHub {
    owner = "CERBSim";
    repo = "webgui_jupyter_widgets";
    rev = "4d5b097a69c3a629a09871de340a853cd499bd30";
    hash = "sha256-KcKDIfPGVyaByTMuOqXOCVIGfQpT5HHiJY+CAZpKwKU=";
    fetchSubmodules = true;
  };

  patches = [
    ./setup.patch
  ];

  preConfigure = ''
    echo "building submodule webgui"
    cd webgui
    yarnOfflineCache=$webguiYarnOfflineCache runHook yarnConfigHook
    yarn --offline build
    cd -
  '';

  webguiYarnOfflineCache = fetchYarnDeps {
    yarnLock = src + "/webgui/yarn.lock";
    hash = "sha256-dW5zbNOpawF64LAaHly02Xgsa8C4seFIXBJLwd8BTVo=";
  };

  yarnOfflineCache = fetchYarnDeps {
    yarnLock = src + "/yarn.lock";
    hash = "sha256-d6s8U7seUO1HWttxJV+1SosnAI6D4xlS5XSObOk3ezo=";
  };

  preBuild = ''
    export PATH=${jupyter}/bin:$PATH
    yarn --offline build:prod
  '';

  build-system = [
    nodejs
    setuptools
    jupyter
    jupyter-packaging
    yarnConfigHook
  ];

  dependencies = [
    numpy
    jupyterlab
    packaging
    jupyterlab-widgets
    ipywidgets
  ];

  pythonImportsCheck = [ "webgui_jupyter_widgets" ];

  meta = {
    description = "Jupyter widgetds library for webgui js visualization library";
    homepage = "https://github.com/CERBSim/webgui_jupyter_widgets";
    license = lib.licenses.lgpl2Plus;
    maintainers = with lib.maintainers; [ qbisi ];
  };
}

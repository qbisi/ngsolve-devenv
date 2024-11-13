{
  buildPythonPackage,
  fetchFromGitHub,
  lib,
  jupyter-packaging,
  setuptools,
  packaging,
  webgui,
  yarnConfigHook,
}:

buildPythonPackage rec {
  pname = "webgui_jupyter_widgets";
  version = "0.2.31";
  pyproject = true;

  src = fetchFromGitHub {
    owner = "CERBSim";
    repo = "webgui_jupyter_widgets";
    rev = "4d5b097a69c3a629a09871de340a853cd499bd30";
    hash = "sha256-ppiytTfySqiWFjCjdQoXXqa9iUqyyuhpKJawQO9IhZ8=";
  };

  build-system = [ setuptools jupyter-packaging ];

  dependencies = [
    packaging
    webgui
  ];


  pythonImportsCheck = [ "webgui_jupyter_widgets" ];

  meta = {
    description = "Jupyter widgetds library for webgui js visualization library";
    homepage = "https://github.com/CERBSim/webgui_jupyter_widgets";
    license = lib.licenses.lgpl2Plus;
    maintainers = with lib.maintainers; [ qbisi ];
  };
}

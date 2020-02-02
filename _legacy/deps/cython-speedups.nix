{ stdenv
, buildPythonPackage
, pycharm
}:

buildPythonPackage rec {
  pname = "cython-speedups";
  version = "1";

  src = "${pycharm}/pycharm-professional-2018.3.4/helpers/pydev/";

  doCheck = false;
}

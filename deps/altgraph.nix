{ buildPythonPackage, fetchPypi }:

buildPythonPackage rec {
  pname = "altgraph";
  version = "0.16.1";

  propagatedBuildInputs = [ ];

  doCheck = false;

  src = fetchPypi {
    inherit pname version;
    sha256 = "034vgy3nnm58rs4a6k83m9imayxx35k0p3hr22wafyql2w035xfx";
  };

}


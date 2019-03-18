{ buildPythonPackage, fetchPypi, pefile, altgraph, macholib }:

buildPythonPackage rec {
  pname = "PyInstaller";
  version = "3.4";

  propagatedBuildInputs = [ pefile altgraph macholib ];

  doCheck = false;

  src = fetchPypi {
    inherit pname version;
    sha256 = "0swq6p5ma6wn38z9df576fzcc6brjfnyp8l93rvgiz5bcr5f19m5";
  };

}


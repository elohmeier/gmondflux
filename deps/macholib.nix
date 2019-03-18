{ buildPythonPackage, fetchPypi, altgraph }:

buildPythonPackage rec {
  pname = "macholib";
  version = "1.11";

  propagatedBuildInputs = [ altgraph ];

  doCheck = false;

  src = fetchPypi {
    inherit pname version;
    sha256 = "1nxr3s2yjc6893hxxmgld1amf7b0dx5zy76qdkdzi6whdzy0y664";
  };

}


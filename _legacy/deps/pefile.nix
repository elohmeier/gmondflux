{ buildPythonPackage, fetchPypi, future }:

buildPythonPackage rec {
  pname = "pefile";
  version = "2018.8.8";

  propagatedBuildInputs = [ future ];

  doCheck = false;

  src = fetchPypi {
    inherit pname version;
    sha256 = "1mkcx182hhm12ry50jpy07gbnp0ihg7pl5lj8m86rjy8w0npwnsc";
  };

}

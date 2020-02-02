{ stdenv, fetchurl, pkgconfig, apr, libconfuse, expat, pcre, zlib, rrdtool }:

stdenv.mkDerivation rec {
  pname = "ganglia";
  version = "3.7.2";

  src = fetchurl {
    url = "mirror://sourceforge/ganglia/ganglia%20monitoring%20core/${version}/ganglia-${version}.tar.gz";
    #url = "https://www.nerdworks.de/aix/ganglia-${version}.tar.gz";
    sha256 = "042dbcaf580a661b55ae4d9f9b3566230b2232169a0898e91a797a4c61888409";
  };

  nativeBuildInputs = [ pkgconfig ];
  buildInputs = [ apr libconfuse expat pcre zlib rrdtool ];
  configureFlags = [ "--with-gmetad" ];

  buildPhase = ''
    make
  '';
}
